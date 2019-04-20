import logging

from telegram.ext import Updater, CommandHandler, MessageHandler, ConversationHandler, RegexHandler, Filters, messagequeue as mq
from telegram import ReplyKeyboardMarkup, ParseMode

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
        entry_points=[RegexHandler('^(Create account)$', account_start)],
        states={
            'account_get_name': [MessageHandler(Filters.text, account_get_name,
                                                pass_user_data=True),
                                 CommandHandler('skip', account_skip_dialog,
                                                pass_user_data=True)],
            'account_get_active': [MessageHandler(Filters.text, account_get_active,
                                                pass_user_data=True),
                                   CommandHandler('skip', account_skip_dialog,
                                                pass_user_data=True)],
            'account_get_owner': [MessageHandler(Filters.text, account_get_owner,
                                                pass_user_data=True),
                                  CommandHandler('skip', account_skip_dialog,
                                                pass_user_data=True)],
            'account_get_payment': [RegexHandler('^(Proceed to checkout)$', account_get_payment, 
                                                pass_user_data=True,
                                                pass_job_queue=True),
                                    CommandHandler('skip', account_skip_dialog,
                                                pass_user_data=True)]
        },
        fallbacks=[MessageHandler(Filters.text, dontknow, pass_user_data=True)])
    dp.add_handler(account)
    dp.add_handler(MessageHandler(Filters.text, dontknow, pass_user_data=True))

    dp.add_error_handler(error)

    mybot.start_polling(timeout=30)
    mybot.idle()


def greet_user(bot, update):
    text = 'Hello. You want create account in EOS blockchain? I can help you!' \
           'I don\'t make money on this, you just pay for basic amount of RAM, CPU and NET.' \
           'IMPORTANT - account creation here is completely safe and transparent.' \
           'The bot doesn\'t have access to your private keys.'
    my_keyboard = ReplyKeyboardMarkup([['Create account']],
        one_time_keyboard=True,
        resize_keyboard=True)
    update.message.reply_text(text, reply_markup=my_keyboard)


def account_start(bot, update):
    text = 'Enter your account name.' \
           'Characters a-z, 1-5 are allowed, account length is exactly 12 lowercase characters.'\
           'To cancel this operation, click /skip'
    update.message.reply_text(text)
    return 'account_get_name'


def account_get_name(bot, update, user_data):
    account_name = update.message.text
    if len(account_name) != 12:
        update.message.reply_text('Account length must be 12 characters. Try again.')
        return 'account_get_name'
    username = ''
    for symbol in account_name:
        if symbol.isalpha() and symbol.islower() or symbol in ['1', '2', '3', '4', '5']:
            username += symbol
        else:
            update.message.reply_text('Invalid account name. Try again.')
            return 'account_get_name'
    availaible = check_account_accessability(username)
    if not availaible:
        update.message.reply_text('This account is already taken, try another name.')
        return 'account_get_name'
    else:
        user_data['account_name'] = username

    update.message.reply_text('You can assign some permissions to account at the EOS blockchain.' \
                              ' This is possible by setting OWNER and ACTIVE keys. With ACTIVE key' \
                              ' you simply can send tokens, purchase RAM, voting and etc.' \
                              ' OWNER key have same permissions as an ACTIVE key and more:' \
                              ' you can change account ownership and other high-level permissions.' \
                              ' It is created for additional security. ACTIVE and OWNER keys can be the same.' \
                              ' If you are a beginner - don\'t worry, you can do the same keys and then, ' \
                              ' when you figure it out, make them different if needed.')

    info_message = 'So now you need to input ACTIVE key.' \
                   ' You can generate it at any convenient service.' \
                   ' For example you can use [EOS-voter](https://github.com/greymass/eos-voter)' \
                   ' or [nadejde](https://nadejde.github.io/eos-token-sale/).' \
                   ' Don\'t forget to save your PRIVATE key. ACTIVE key and PRIVATE keys are not the same!' \
                   ' This is IMPORTANT! To cancel this operation, click /skip'

    bot.sendMessage(chat_id=update.message.chat_id, 
                    text=info_message,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True)

    return 'account_get_active'


def account_get_active(bot, update, user_data):
    active_key = update.message.text
    if active_key.find('EOS') == -1:
        update.message.reply_text('Invalid ACTIVE key')
        return 'account_get_active'
    elif active_key.find('EOS') >= 0:
        result = verification_pubkey(active_key)
        if result:
            user_data['active_key'] = active_key
            info_message = 'Now you need input OWNER key. It can be the same as ACTIVE key.' \
                           ' You still can generate it at [EOS-voter](https://github.com/greymass/eos-voter)' \
                           ' or [nadejde](https://nadejde.github.io/eos-token-sale/).' \
                           ' To cancel this operation, click /skip'
            bot.sendMessage(chat_id=update.message.chat_id,
                            text=info_message, parse_mode=ParseMode.MARKDOWN,
                            disable_web_page_preview=True)
            return 'account_get_owner'
        else:
            update.message.reply_text('Invalid key.')
            return 'account_get_active'
        

def account_get_owner(bot, update, user_data):
    owner_key = update.message.text
    if owner_key.find('EOS') == -1:
        update.message.reply_text('Invalid OWNER key.')
        return 'account_get_owner'
    elif owner_key.find('EOS') >= 0:
        result = verification_pubkey(owner_key)
        if result:
            user_data['owner_key'] = owner_key
            my_keyboard = ReplyKeyboardMarkup([['Proceed to checkout']],
                    one_time_keyboard=True,
                    resize_keyboard=True)
            update.message.reply_text('Great. I have all the data and ready to create your account.' \
                                      ' Now you need just pay some small costs for RAM, CPU and NET.' \
                                      ' To cancel this operation, click /skip', 
                                       reply_markup=my_keyboard)
            return 'account_get_payment'
            
        else:
            update.message.reply_text('Invalid key.')
            return 'account_get_owner'


def account_get_payment(bot, update, user_data, job_queue):
    update.message.reply_text('Great! Now i will generate payment link')
    order_id = f'vz{id_generator()}'
    payment_data = create_order(order_id)
    user_data['order_id'] = payment_data['id']
    create_job(bot, update, job_queue, user_data)
    update.message.reply_text('The order is valid for 15 minutes. It takes some time to process the payment,' \
                               f' so don\'t worry, everything works fine.\n{payment_data["url"]} ')


@mq.queuedmessage
def check_payment_status(bot, job):
    order_status = get_order_status(job.context['order_id'])
    if order_status == 'expired':
        bot.sendMessage(chat_id=job.context['chat_id'],
                        text='Order has expired, click /start if you want try again.')

        return ConversationHandler.END
    elif order_status == 'completed':
        job.schedule_removal()
        bot.sendMessage(chat_id=job.context['chat_id'],
                        text='Payment received, account creating...')
        transaction_id = create_eos_acc(
            account_name=job.context['account_name'],
            activekey=job.context['active_key'],
            ownerkey=job.context['owner_key']
        )
        info_message = 'You need a wallet for comfortable work with EOS.' \
                       ' We recommend [EOS-voter](https://github.com/greymass/eos-voter)' \
                       ' or [Scatter](https://github.com/GetScatter/ScatterDesktop/releases).' \
                       ' Enjoy!' \
                       ' Сlick /start if you want try again.'

        bot.sendMessage(chat_id=job.context['chat_id'], 
                        text=f'https://jungle.bloks.io/transaction/{transaction_id}')

        bot.sendMessage(chat_id=job.context['chat_id'], 
                        text=info_message, 
                        parse_mode=ParseMode.MARKDOWN, 
                        disable_web_page_preview=True)
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
    text = '''We decided to skip the creation of an account. Click /start if you want try again.'''
    update.message.reply_text(text)
    return ConversationHandler.END


def dontknow(bot, update, user_data):
    update.message.reply_text('Please follow the instructions.')


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning(f'Update {update} caused error {error}')


if __name__ == '__main__':
    main()
