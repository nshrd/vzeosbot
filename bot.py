import logging

from eospy.cleos import Cleos
from telegram.ext import Updater, CommandHandler, MessageHandler, ConversationHandler, RegexHandler, Filters, messagequeue as mq
from telegram import ReplyKeyboardMarkup, KeyboardButton

from utils import verification_pubkey, check_account_accessability, create_eos_acc
from alfacoins import create_order, get_order_status, id_generator

import config


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG,
                    filename='bot.log'
                    )

logger = logging.getLogger(__name__)


def main():
    mybot = Updater(config.API_KEY, request_kwargs=config.PROXY)
    
    dp = mybot.dispatcher

    mybot.bot._msg_queue = mq.MessageQueue()
    mybot.bot._is_messages_queued_default = True

    dp.add_handler(CommandHandler('start', greet_user))
    account = ConversationHandler(
        entry_points=[RegexHandler('^(Создать аккаунт)$', account_start)],
        states={
            'account_get_name': [MessageHandler(Filters.text, account_get_name, pass_user_data=True),
                                 CommandHandler('cancel', account_skip_dialog, pass_user_data=True)],
            'account_get_active': [MessageHandler(Filters.text, account_get_active, pass_user_data=True),
                                   CommandHandler('cancel', account_skip_dialog, pass_user_data=True)],
            'account_get_owner': [MessageHandler(Filters.text, account_get_owner, pass_user_data=True),
                                  CommandHandler('cancel', account_skip_dialog, pass_user_data=True)],
            'account_get_payment': [RegexHandler('^(Перейти к оплате)$', account_get_payment, pass_user_data=True, pass_job_queue=True)]
        },
        fallbacks=[MessageHandler(Filters.text, dontknow, pass_user_data=True)])
    dp.add_handler(account)
    dp.add_handler(MessageHandler(Filters.text, dontknow, pass_user_data=True))

    dp.add_error_handler(error)

    mybot.start_polling(timeout=30)
    mybot.idle()


def greet_user(bot, update):
    text = '''Привет. Ты хочешь создать аккаунт ЕОС? Тогда ты по адресу. Я не зарабатываю на этом, ты просто оплачиваешь покупку RAM и минимальное количество CPU и NET. Приступим?'''
    my_keyboard = ReplyKeyboardMarkup([['Создать аккаунт']],
        one_time_keyboard=True,
        resize_keyboard=True)
    update.message.reply_text(text, reply_markup=my_keyboard)


def account_start(bot, update):
    text = '''Введи название аккаунта. Допускаются символы a-z, 1-5, длина аккаунта ровно 12 символов в нижнем регистре. Чтобы отменить данную операцию нажми /cancel '''
    update.message.reply_text(text)
    return 'account_get_name'


def account_get_name(bot, update, user_data):
    print(user_data)
    account_name = update.message.text
    if len(account_name) != 12:
        update.message.reply_text('Длина аккаунта должна быть 12 символов. Попробу еще раз')
        return 'account_get_name'
    username = ''
    for symbol in account_name:
        if symbol.isalpha() and symbol.islower() or symbol in ['1', '2', '3', '4', '5']:
            username += symbol
        else:
            update.message.reply_text('Недопустимое имя аккаунта. Попробуй ещё раз')
            return 'account_get_name'
    availaible = check_account_accessability(username)
    if not availaible:
        update.message.reply_text('Данный аккаунт уже занят, попробу другой')
        return 'account_get_name'
    else:
        user_data['account_name'] = username

    update.message.reply_text('Теперь нужно ввести public key. Чтобы отменить данную операцию нажми /cancel')
    return 'account_get_active'


def account_get_active(bot, update, user_data):
    active_key = update.message.text
    if active_key.find('EOS') == -1:
        update.message.reply_text('Некорректный public key')
        return 'account_get_active'
    elif active_key.find('EOS') >= 0:
        result = verification_pubkey(active_key)
        if result:
            user_data['active_key'] = active_key
            update.message.reply_text('Теперь нужно ввести owner key. Чтобы отменить данную операцию нажми /cancel')
            return 'account_get_owner'
        else:
            update.message.reply_text('Некорректный ключ')
            return 'account_get_active'
        

def account_get_owner(bot, update, user_data):
    owner_key = update.message.text
    if owner_key.find('EOS') == -1:
        update.message.reply_text('Некорректный owner key')
        return 'account_get_owner'
    elif owner_key.find('EOS') >= 0:
        result = verification_pubkey(owner_key)
        if result:
            user_data['owner_key'] = owner_key
            my_keyboard = ReplyKeyboardMarkup([['Перейти к оплате']],
                    one_time_keyboard=True,
                    resize_keyboard=True)
            update.message.reply_text('Отлично, я поулчил все необходимые данные, теперь необходимо оплатить мелкие расходы и аккаунт готов', reply_markup=my_keyboard)
            return 'account_get_payment'
            
        else:
            update.message.reply_text('Некорректный ключ')
            return 'account_get_owner'


def account_get_payment(bot, update, user_data, job_queue):
    update.message.reply_text('Отлично, сейчас я сгенерирую ссылку для оплаты')
    order_id = f'vz{id_generator()}'
    payment_data = create_order(order_id)
    user_data['order_id'] = payment_data['id']
    create_job(bot, update, job_queue, user_data)
    update.message.reply_text(f'Ордер действителен втечение 15 минут. На проведение платежа необходимо некоторое время, поэтому не переживай, все работает.\n {payment_data["url"]}')


@mq.queuedmessage
def check_payment_status(bot, job):
    order_status = get_order_status(job.context['order_id'])
    print(order_status)
    print(type(order_status))
    if order_status == 'expired':
        bot.sendMessage(chat_id=job.context['chat_id'], text='Ордер истек, чтобы начать процедуру заново просто нажми /start')
        return ConversationHandler.END
    elif order_status == 'completed':
        job.schedule_removal()
        bot.sendMessage(chat_id=job.context['chat_id'], text='Оплата получена, аккаунт создается...')
        transaction_id = create_eos_acc(
            account_name=job.context['account_name'],
            activekey=job.context['active_key'],
            ownerkey=job.context['owner_key']
        )

        bot.sendMessage(chat_id=job.context['chat_id'], text=f'https://jungle.bloks.io/transaction/{transaction_id}')
        return ConversationHandler.END


def create_job(bot, update, job_queue, user_data):
    job_queue.run_repeating(check_payment_status, interval=60, context={
        'chat_id': update.message.chat_id,
        'order_id': user_data['order_id'],
        'account_name': user_data['account_name'],
        'active_key': user_data['active_key'],
        'owner_key': user_data['owner_key']
        })


def account_skip_dialog(bot, update, user_data):
    text = '''Мы решили отменить создание аккаунта . Чтобы возобновить процедуру нужно вызвать команду /start'''
    update.message.reply_text(text)
    return ConversationHandler.END


def dontknow(bot, update, user_data):
    update.message.reply_text('Пожалуйста, следуй инструкциям.')


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning(f'Update {update} caused error {error}')


if __name__ == '__main__':
    main()
