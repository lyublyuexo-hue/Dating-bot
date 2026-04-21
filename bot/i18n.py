"""
Все тексты бота на двух языках.
Использование:
    from bot.i18n import t
    text = t("welcome", lang)
    text = t("profile_caption", lang, name="Алишер", age=22, city="Ташкент")
"""

TEXTS = {

    # ── Общее ──────────────────────────────────────────────────────────────
    "choose_language": {
        "ru": "🌐 Выбери язык:",
        "uz": "🌐 Tilni tanlang:",
    },
    "language_set_ru": {
        "ru": "✅ Язык изменён на Русский",
        "uz": "✅ Til ruscha qilib o'zgartirildi",
    },
    "language_set_uz": {
        "ru": "✅ Til o'zbekchaga o'zgartirildi",
        "uz": "✅ Til o'zbekchaga o'zgartirildi",
    },

    # ── Регистрация ─────────────────────────────────────────────────────────
    "reg_welcome": {
        "ru": (
            "Привет! 👋\n\n"
            "Я помогу тебе найти собеседника или вторую половинку 💘\n\n"
            "Сначала выбери язык:"
        ),
        "uz": (
            "Salom! 👋\n\n"
            "Men senga do'st yoki sevgilini topishda yordam beraman 💘\n\n"
            "Avval tilni tanlang:"
        ),
    },
    "reg_ask_name": {
        "ru": "Как тебя зовут? Введи имя:",
        "uz": "Ismingiz nima? Ismingizni kiriting:",
    },
    "reg_ask_gender": {
        "ru": "Отлично, {name}! Кто ты?",
        "uz": "Zo'r, {name}! Siz kimsiz?",
    },
    "reg_ask_age": {
        "ru": "Сколько тебе лет?",
        "uz": "Yoshingiz nechida?",
    },
    "reg_age_error": {
        "ru": "Введи корректный возраст (14–100):",
        "uz": "To'g'ri yoshni kiriting (14–100):",
    },
    "reg_ask_city": {
        "ru": "Из какого ты города?",
        "uz": "Qaysi shahardasiz?",
    },
    "reg_ask_photo": {
        "ru": "Загрузи своё фото 📸\n\nОно будет видно другим пользователям.",
        "uz": "Rasmingizni yuklang 📸\n\nBoshqa foydalanuvchilar uni ko'radi.",
    },
    "reg_photo_error": {
        "ru": "Пожалуйста, отправь фото, а не текст.",
        "uz": "Iltimos, matn emas, rasm yuboring.",
    },
    "reg_ask_about": {
        "ru": "Расскажи немного о себе 📝\n\nИли напиши «-» чтобы пропустить:",
        "uz": "O'zingiz haqingizda qisqacha yozing 📝\n\nYoki o'tkazib yuborish uchun «-» yozing:",
    },
    "reg_ask_looking": {
        "ru": "Кого ищешь?",
        "uz": "Kimni qidiryapsiz?",
    },
    "reg_ask_tags": {
        "ru": "Выбери свои интересы 🎯\n\nМожно выбрать несколько. Нажми «Готово» когда закончишь:",
        "uz": "Qiziqishlaringizni tanlang 🎯\n\nBirnechtasini tanlash mumkin. Tugatgach «Tayyor» tugmasini bosing:",
    },
    "reg_done": {
        "ru": (
            "🎉 Анкета создана, {name}!\n\n"
            "Теперь ты можешь смотреть анкеты других и знакомиться."
        ),
        "uz": (
            "🎉 Anketa yaratildi, {name}!\n\n"
            "Endi boshqalarning anketalarini ko'rib, tanishishingiz mumkin."
        ),
    },
    "reg_already": {
        "ru": "Ты уже зарегистрирован! Используй меню ниже.",
        "uz": "Siz allaqachon ro'yxatdan o'tgansiz! Quyidagi menyudan foydalaning.",
    },
    "reg_cancelled": {
        "ru": "Регистрация отменена. Напиши /start чтобы начать заново.",
        "uz": "Ro'yxatdan o'tish bekor qilindi. Qaytadan boshlash uchun /start yozing.",
    },

    # ── Кнопки регистрации ──────────────────────────────────────────────────
    "btn_male": {
        "ru": "👨 Парень",
        "uz": "👨 Yigit",
    },
    "btn_female": {
        "ru": "👩 Девушка",
        "uz": "👩 Qiz",
    },
    "btn_looking_male": {
        "ru": "👨 Парней",
        "uz": "👨 Yigitlar",
    },
    "btn_looking_female": {
        "ru": "👩 Девушек",
        "uz": "👩 Qizlar",
    },
    "btn_looking_all": {
        "ru": "🌈 Всех",
        "uz": "🌈 Barchasi",
    },
    "btn_done": {
        "ru": "✔️ Готово",
        "uz": "✔️ Tayyor",
    },
    "btn_back": {
        "ru": "◀️ Назад",
        "uz": "◀️ Orqaga",
    },
    "btn_cancel": {
        "ru": "❌ Отмена",
        "uz": "❌ Bekor qilish",
    },
    "btn_skip": {
        "ru": "➡️ Пропустить",
        "uz": "➡️ O'tkazib yuborish",
    },

    # ── Главное меню (Reply-кнопки) ─────────────────────────────────────────
    "menu_browse": {
        "ru": "👀 Смотреть анкеты",
        "uz": "👀 Anketalarni ko'rish",
    },
    "menu_search": {
        "ru": "🔍 Поиск",
        "uz": "🔍 Qidiruv",
    },
    "menu_favorites": {
        "ru": "⭐ Избранные",
        "uz": "⭐ Sevimlilar",
    },
    "menu_referral": {
        "ru": "🔗 Реферал",
        "uz": "🔗 Referal",
    },
    "menu_profile": {
        "ru": "👤 Мой профиль",
        "uz": "👤 Mening anketam",
    },

    # ── Главный экран (inline) ──────────────────────────────────────────────
    "home_text": {
        "ru": (
            "<b>Главное меню</b>\n\n"
            "👀 <b>Смотреть анкеты</b> — найди нового человека\n\n"
            "👤 <b>Мой профиль</b> — посмотри и отредактируй\n\n"
            "🙈 <b>Скрыть анкету</b> — временно исчезнуть из поиска\n\n"
            "⭐ <b>Premium</b> — будь в топе и найди быстрее"
        ),
        "uz": (
            "<b>Asosiy menyu</b>\n\n"
            "👀 <b>Anketalarni ko'rish</b> — yangi odam topish\n\n"
            "👤 <b>Mening anketam</b> — ko'rish va tahrirlash\n\n"
            "🙈 <b>Anketani yashirish</b> — qidiruvdan vaqtincha chiqish\n\n"
            "⭐ <b>Premium</b> — tepada bo'l, tezroq top"
        ),
    },
    "btn_home_browse": {
        "ru": "👀 Смотреть анкеты",
        "uz": "👀 Anketalarni ko'rish",
    },
    "btn_home_profile": {
        "ru": "👤 Мой профиль",
        "uz": "👤 Mening anketam",
    },
    "btn_home_hide": {
        "ru": "🙈 Скрыть анкету",
        "uz": "🙈 Anketani yashirish",
    },
    "btn_home_premium": {
        "ru": "⭐ Получить Premium",
        "uz": "⭐ Premium olish",
    },
    "home_hidden": {
        "ru": "😔 Анкета скрыта. Чтобы снова появиться в поиске — напиши /start",
        "uz": "😔 Anketa yashirildi. Qidiruvga qaytish uchun /start yozing.",
    },

    # ── Просмотр анкет ──────────────────────────────────────────────────────
    "browse_empty": {
        "ru": "😢 Анкеты закончились. Загляни позже — появятся новые!",
        "uz": "😢 Anketalar tugadi. Keyinroq qarang — yangilari paydo bo'ladi!",
    },
    "browse_caption": {
        "ru": "{boost}<b>{name}, {age}</b> — {city}\n{verified}\n\n{about}\n\n🎯 Интересы: {tags}",
        "uz": "{boost}<b>{name}, {age}</b> — {city}\n{verified}\n\n{about}\n\n🎯 Qiziqishlar: {tags}",
    },
    "browse_no_tags": {
        "ru": "не указаны",
        "uz": "ko'rsatilmagan",
    },
    "browse_verified": {
        "ru": "✅ Верифицирован",
        "uz": "✅ Tasdiqlangan",
    },
    "btn_like": {
        "ru": "❤️",
        "uz": "❤️",
    },
    "btn_fav": {
        "ru": "⭐",
        "uz": "⭐",
    },
    "btn_skip_profile": {
        "ru": "👎",
        "uz": "👎",
    },
    "btn_report": {
        "ru": "🚨",
        "uz": "🚨",
    },
    "like_sent": {
        "ru": "Лайк отправлен ❤️",
        "uz": "Layk yuborildi ❤️",
    },
    "skipped": {
        "ru": "Пропущено 👎",
        "uz": "O'tkazib yuborildi 👎",
    },
    "match_notify": {
        "ru": "💘 Мэтч с <b>{name}</b>! Пиши: @{username}{common}",
        "uz": "💘 <b>{name}</b> bilan match! Yozing: @{username}{common}",
    },
    "match_username_none": {
        "ru": "напрямую",
        "uz": "to'g'ridan-to'g'ri",
    },
    "match_common_tags": {
        "ru": "\n\n🎯 Общие интересы: {tags}",
        "uz": "\n\n🎯 Umumiy qiziqishlar: {tags}",
    },

    # ── Жалобы ──────────────────────────────────────────────────────────────
    "report_choose": {
        "ru": "Выбери причину жалобы:",
        "uz": "Shikoyat sababini tanlang:",
    },
    "report_sent": {
        "ru": "✅ Жалоба отправлена. Модератор рассмотрит её в ближайшее время.",
        "uz": "✅ Shikoyat yuborildi. Moderator uni ko'rib chiqadi.",
    },
    "report_reasons": {
        "ru": ["Фейк/мошенник", "Оскорбления", "Спам", "Несовершеннолетний", "Другое"],
        "uz": ["Soxta/firibgar", "Haqorat", "Spam", "Voyaga etmagan", "Boshqa"],
    },

    # ── Профиль ─────────────────────────────────────────────────────────────
    "profile_caption": {
        "ru": (
            "<b>Твой профиль</b>\n\n"
            "👤 {name}, {age} — {city}\n"
            "{verified}\n"
            "🏆 Активность: {score} очков\n\n"
            "📝 {about}\n\n"
            "🎯 Интересы: {tags}"
        ),
        "uz": (
            "<b>Mening anketam</b>\n\n"
            "👤 {name}, {age} — {city}\n"
            "{verified}\n"
            "🏆 Faollik: {score} ball\n\n"
            "📝 {about}\n\n"
            "🎯 Qiziqishlar: {tags}"
        ),
    },
    "profile_no_about": {
        "ru": "Описание не указано",
        "uz": "Tavsif kiritilmagan",
    },
    "profile_no_tags": {
        "ru": "не выбраны",
        "uz": "tanlanmagan",
    },
    "profile_not_found": {
        "ru": "Сначала зарегистрируйся через /start",
        "uz": "Avval /start orqali ro'yxatdan o'ting",
    },
    "profile_hidden_by_user": {
        "ru": "🙈 Анкета скрыта от других пользователей",
        "uz": "🙈 Anketa boshqa foydalanuvchilardan yashirilgan",
    },
    "btn_profile_edit":    {"ru": "✏️ Редактировать", "uz": "✏️ Tahrirlash"},
    "btn_profile_photo":   {"ru": "📸 Сменить фото",  "uz": "📸 Rasmni o'zgartirish"},
    "btn_profile_preview": {"ru": "👀 Предпросмотр",  "uz": "👀 Ko'rib chiqish"},
    "btn_profile_delete":  {"ru": "🗑 Удалить анкету", "uz": "🗑 Anketani o'chirish"},
    "btn_profile_show":    {"ru": "👁 Показать анкету", "uz": "👁 Anketani ko'rsatish"},
    "btn_profile_verify":  {"ru": "📸 Верифицировать", "uz": "📸 Tasdiqlash"},

    "profile_edit_choose": {
        "ru": "Что хочешь изменить?",
        "uz": "Nimani o'zgartirmoqchisiz?",
    },
    "btn_edit_name":    {"ru": "👤 Имя",       "uz": "👤 Ism"},
    "btn_edit_age":     {"ru": "🎂 Возраст",   "uz": "🎂 Yosh"},
    "btn_edit_city":    {"ru": "🌆 Город",     "uz": "🌆 Shahar"},
    "btn_edit_about":   {"ru": "📝 О себе",    "uz": "📝 O'zim haqimda"},
    "btn_edit_tags":    {"ru": "🎯 Интересы",  "uz": "🎯 Qiziqishlar"},
    "btn_edit_looking": {"ru": "🔍 Ищу кого",  "uz": "🔍 Kimni qidiraman"},

    "edit_ask_name":    {"ru": "Введи новое имя:",         "uz": "Yangi ismingizni kiriting:"},
    "edit_ask_age":     {"ru": "Введи новый возраст:",     "uz": "Yangi yoshingizni kiriting:"},
    "edit_ask_city":    {"ru": "Введи новый город:",       "uz": "Yangi shahringizni kiriting:"},
    "edit_ask_about":   {"ru": "Напиши о себе (или «-» чтобы убрать):", "uz": "O'zingiz haqingizda yozing (yoki «-» o'chirish uchun):"},
    "edit_ask_photo":   {"ru": "Отправь новое фото 📸",    "uz": "Yangi rasmingizni yuboring 📸"},
    "edit_ask_looking": {"ru": "Кого ищешь?",              "uz": "Kimni qidiryapsiz?"},
    "edit_saved":       {"ru": "✅ Сохранено!",            "uz": "✅ Saqlandi!"},
    "edit_age_error":   {"ru": "Введи корректный возраст (14–100):", "uz": "To'g'ri yoshni kiriting (14–100):"},

    "profile_delete_confirm": {
        "ru": "⚠️ Удалить анкету? Это действие необратимо.",
        "uz": "⚠️ Anketani o'chirasizmi? Bu amalni qaytarib bo'lmaydi.",
    },
    "btn_delete_yes": {"ru": "🗑 Да, удалить", "uz": "🗑 Ha, o'chirish"},
    "btn_delete_no":  {"ru": "◀️ Отмена",      "uz": "◀️ Bekor qilish"},
    "profile_deleted": {
        "ru": "Анкета удалена. Напиши /start чтобы создать новую.",
        "uz": "Anketa o'chirildi. Yangi yaratish uchun /start yozing.",
    },

    # ── Верификация ─────────────────────────────────────────────────────────
    "verify_already": {
        "ru": "⏳ Заявка на верификацию уже отправлена, ожидай.",
        "uz": "⏳ Tasdiqlash so'rovi allaqachon yuborilgan, kuting.",
    },
    "verify_request": {
        "ru": (
            "📸 <b>Верификация фото</b>\n\n"
            "Отправь видео-кружок (🔵) с твоим лицом.\n"
            "Это докажет что ты реальный человек.\n\n"
            "После проверки ты получишь значок ✅ на анкете."
        ),
        "uz": (
            "📸 <b>Foto tasdiqlash</b>\n\n"
            "Yuzingiz ko'rinadigan video-doira (🔵) yuboring.\n"
            "Bu siz haqiqiy odam ekanligingizni isbotlaydi.\n\n"
            "Tekshiruvdan so'ng anketangizda ✅ belgisi paydo bo'ladi."
        ),
    },
    "verify_approved": {
        "ru": "✅ Верификация прошла успешно! На анкете теперь есть значок ✅",
        "uz": "✅ Tasdiqlash muvaffaqiyatli o'tdi! Anketada endi ✅ belgisi bor.",
    },
    "verify_rejected": {
        "ru": "❌ Верификация отклонена. Попробуй снова — отправь чёткое видео-кружок с лицом.",
        "uz": "❌ Tasdiqlash rad etildi. Qaytadan urinib ko'ring — aniq yuz ko'rinadigan video-doira yuboring.",
    },

    # ── Верификация — статусы ────────────────────────────────────────────────
    "ver_none":     {"ru": "",                  "uz": ""},
    "ver_pending":  {"ru": "⏳ На проверке",    "uz": "⏳ Tekshirilmoqda"},
    "ver_verified": {"ru": "✅ Верифицирован",  "uz": "✅ Tasdiqlangan"},
    "ver_rejected": {"ru": "❌ Отклонено",      "uz": "❌ Rad etildi"},

    # ── Поиск ───────────────────────────────────────────────────────────────
    "search_premium_only": {
        "ru": "🔒 <b>Поиск</b> доступен только Premium пользователям.\n\nАктивируй подписку — нажми «⭐ Получить Premium»",
        "uz": "🔒 <b>Qidiruv</b> faqat Premium foydalanuvchilar uchun mavjud.\n\nObunani faollashtiring — «⭐ Premium olish» tugmasini bosing",
    },
    "search_choose_mode": {
        "ru": "🔍 <b>Поиск</b>\n\nКак будем искать?",
        "uz": "🔍 <b>Qidiruv</b>\n\nQanday qidiramiz?",
    },
    "btn_search_tag":  {"ru": "🏷 По тегу",   "uz": "🏷 Teg bo'yicha"},
    "btn_search_city": {"ru": "🌆 По городу", "uz": "🌆 Shahar bo'yicha"},
    "search_by_tag": {
        "ru": "🏷 <b>Поиск по тегу</b>\n\nВыбери интерес:",
        "uz": "🏷 <b>Teg bo'yicha qidiruv</b>\n\nQiziqishni tanlang:",
    },
    "search_by_city": {
        "ru": "🌆 <b>Поиск по городу</b>\n\nВведи название города:",
        "uz": "🌆 <b>Shahar bo'yicha qidiruv</b>\n\nShahar nomini kiriting:",
    },
    "search_empty_tag": {
        "ru": "По тегу «{tag}» никого не найдено 😔",
        "uz": "«{tag}» tegi bo'yicha hech kim topilmadi 😔",
    },
    "search_empty_city": {
        "ru": "В городе «{city}» никого не найдено 😔",
        "uz": "«{city}» shahrida hech kim topilmadi 😔",
    },
    "search_found_tag": {
        "ru": "🔍 По тегу <b>{tag}</b> найдено {count} человек:",
        "uz": "🔍 <b>{tag}</b> tegi bo'yicha {count} kishi topildi:",
    },
    "search_found_city": {
        "ru": "🌆 В городе <b>{city}</b> найдено {count} человек:",
        "uz": "🌆 <b>{city}</b> shahrida {count} kishi topildi:",
    },

    # ── Избранное ────────────────────────────────────────────────────────────
    "favorites_empty": {
        "ru": "⭐ У тебя пока нет избранных.\n\nНажми ⭐ под любой анкетой чтобы добавить.",
        "uz": "⭐ Hali sevimlilaring yo'q.\n\nQo'shish uchun istalgan anketa ostidagi ⭐ tugmasini bosing.",
    },
    "favorites_caption": {
        "ru": "⭐ <b>Избранные {current}/{total}</b>\n\n<b>{name}, {age}</b> — {city}\n{verified}\n\n{about}",
        "uz": "⭐ <b>Sevimlilar {current}/{total}</b>\n\n<b>{name}, {age}</b> — {city}\n{verified}\n\n{about}",
    },
    "fav_added":   {"ru": "Добавлено в избранное ⭐",  "uz": "Sevimlilarga qo'shildi ⭐"},
    "fav_already": {"ru": "Уже в избранном ⭐",        "uz": "Allaqachon sevimlilarda ⭐"},
    "fav_limit": {
        "ru": "Лимит {limit} анкет. Активируй Premium для безлимита ⭐",
        "uz": "Chegara {limit} ta anketa. Chegarasiz uchun Premium faollashtiring ⭐",
    },
    "fav_removed":  {"ru": "Удалено из избранного 🗑", "uz": "Sevimlilardan o'chirildi 🗑"},
    "fav_list_empty": {
        "ru": "⭐ Избранных больше нет.",
        "uz": "⭐ Sevimlilar endi yo'q.",
    },
    "btn_fav_write":  {"ru": "💬 Написать", "uz": "💬 Yozish"},
    "btn_fav_remove": {"ru": "🗑 Удалить",  "uz": "🗑 O'chirish"},

    # ── Реферал ─────────────────────────────────────────────────────────────
    "referral_text": {
        "ru": (
            "🔗 <b>Реферальная программа</b>\n\n"
            "Приглашено друзей: <b>{invited}</b>\n"
            "До следующего буста: <b>{next_boost}</b> чел.{boost_active}\n\n"
            "За каждые <b>3 приглашения</b> твоя анкета получает\n"
            "<b>+7 дней буста</b> — чаще показывается другим ❤️\n\n"
            "Твоя ссылка:"
        ),
        "uz": (
            "🔗 <b>Referal dasturi</b>\n\n"
            "Taklif qilingan do'stlar: <b>{invited}</b>\n"
            "Keyingi bustgacha: <b>{next_boost}</b> kishi{boost_active}\n\n"
            "Har <b>3 ta taklif</b> uchun anketangiz\n"
            "<b>+7 kun bust</b> oladi — boshqalarga ko'proq ko'rinadi ❤️\n\n"
            "Sizning havolangiz:"
        ),
    },
    "referral_boost_active": {
        "ru": "\n⚡ <b>Буст активен</b> до {date}",
        "uz": "\n⚡ <b>Bust faol</b> {date} gacha",
    },
    "btn_referral_share": {
        "ru": "📤 Поделиться ссылкой",
        "uz": "📤 Havolani ulashish",
    },
    "referral_invited": {
        "ru": "🎉 По твоей ссылке зарегистрировался новый пользователь!\nВсего приглашено: <b>{count}</b>{boost}",
        "uz": "🎉 Havolangiz orqali yangi foydalanuvchi ro'yxatdan o'tdi!\nJami taklif qilingan: <b>{count}</b>{boost}",
    },
    "referral_boost_earned": {
        "ru": "\n🚀 Ты получил +{days} дней буста!",
        "uz": "\n🚀 Siz +{days} kun bust oldingiz!",
    },

    # ── Premium ──────────────────────────────────────────────────────────────
    "premium_text": {
        "ru": (
            "⭐ <b>Premium подписка</b>\n\n"
            "• Анкета показывается первой в поиске\n"
            "• Поиск людей по тегу и городу\n"
            "• Безлимитное избранное\n"
            "• Значок ⭐ на профиле\n"
            "• Видишь кто тебя лайкнул\n\n"
            "Выбери тариф:"
        ),
        "uz": (
            "⭐ <b>Premium obuna</b>\n\n"
            "• Anketa qidiruvda birinchi ko'rsatiladi\n"
            "• Teg va shahar bo'yicha qidiruv\n"
            "• Chegarasiz sevimlilar\n"
            "• Profilda ⭐ belgisi\n"
            "• Kim layk bosganini ko'rasan\n\n"
            "Tarifni tanlang:"
        ),
    },
    "btn_premium_1m": {"ru": "⭐ 1 месяц — 30 000 сум",      "uz": "⭐ 1 oy — 30 000 so'm"},
    "btn_premium_3m": {"ru": "⭐⭐ 3 месяца — 70 000 сум",   "uz": "⭐⭐ 3 oy — 70 000 so'm"},
    "btn_premium_1y": {"ru": "⭐⭐⭐ 1 год — 250 000 сум",   "uz": "⭐⭐⭐ 1 yil — 250 000 so'm"},
    "premium_payment": {
        "ru": (
            "💳 <b>Оплата Premium — {label}</b>\n\n"
            "Сумма: <b>{price}</b>\n\n"
            "📍 <b>Номер карты:</b>\n<code>{card}</code>\n\n"
            "⚠️ <b>Инструкция:</b>\n"
            "1️⃣ Скопируй номер карты\n"
            "2️⃣ Переведи <b>{price}</b> на карту\n"
            "3️⃣ Сделай скриншот чека\n"
            "4️⃣ Нажми кнопку ниже и отправь скриншот\n\n"
            "⏳ Активация в течение 15 минут"
        ),
        "uz": (
            "💳 <b>Premium to'lovi — {label}</b>\n\n"
            "Summa: <b>{price}</b>\n\n"
            "📍 <b>Karta raqami:</b>\n<code>{card}</code>\n\n"
            "⚠️ <b>Ko'rsatma:</b>\n"
            "1️⃣ Karta raqamini nusxa oling\n"
            "2️⃣ <b>{price}</b> kartaga o'tkaring\n"
            "3️⃣ Chek skrinshotini oling\n"
            "4️⃣ Quyidagi tugmani bosib skrinshotni yuboring\n\n"
            "⏳ 15 daqiqa ichida faollashtirish"
        ),
    },
    "btn_pay_confirm": {
        "ru": "✅ Я оплатил — отправить чек",
        "uz": "✅ To'ladim — chekni yuborish",
    },
    "premium_awaiting_receipt": {
        "ru": "📸 Отправьте скриншот чека об оплате.\n\nПосле проверки Premium будет активирован.",
        "uz": "📸 To'lov chekining skrinshotini yuboring.\n\nTekshiruvdan so'ng Premium faollashtiriladi.",
    },
    "premium_receipt_received": {
        "ru": "✅ Чек получен! Ожидайте активации в течение 15 минут.\n\nВопросы: @admin",
        "uz": "✅ Chek qabul qilindi! 15 daqiqa ichida faollashtirishni kuting.\n\nSavollar: @admin",
    },
    "premium_given": {
        "ru": "🎉 Вам выдан <b>Premium на {days} дней</b>! ⭐",
        "uz": "🎉 Sizga <b>{days} kunlik Premium</b> berildi! ⭐",
    },

    # ── Онбординг ───────────────────────────────────────────────────────────
    "onboarding_1": {
        "ru": (
            "👀 <b>Как смотреть анкеты?</b>\n\n"
            "Нажми <b>«👀 Смотреть анкеты»</b> в меню.\n"
            "❤️ — лайк, 👎 — пропустить, ⭐ — в избранное, 🚨 — пожаловаться.\n\n"
            "Если оба поставят лайк — это мэтч! Вы сможете написать друг другу."
        ),
        "uz": (
            "👀 <b>Anketalarni qanday ko'rish?</b>\n\n"
            "Menyudagi <b>«👀 Anketalarni ko'rish»</b> tugmasini bosing.\n"
            "❤️ — layk, 👎 — o'tkazib yuborish, ⭐ — sevimlilarga, 🚨 — shikoyat.\n\n"
            "Ikkalangiz ham layk qo'ysangiz — bu match! Bir-biringizga yoza olasizlar."
        ),
    },
    "onboarding_2": {
        "ru": (
            "⭐ <b>Premium — больше возможностей</b>\n\n"
            "С Premium твоя анкета показывается первой, "
            "можешь искать по городу и тегам, "
            "и видеть кто тебя лайкнул.\n\n"
            "Нажми «⭐ Получить Premium» в главном меню чтобы узнать подробнее."
        ),
        "uz": (
            "⭐ <b>Premium — ko'proq imkoniyatlar</b>\n\n"
            "Premium bilan anketangiz birinchi ko'rsatiladi, "
            "shahar va teg bo'yicha qidirish mumkin, "
            "va kim layk bosganini ko'rish mumkin.\n\n"
            "Batafsil ma'lumot uchun asosiy menyudagi «⭐ Premium olish» tugmasini bosing."
        ),
    },

    # ── Блокировка ──────────────────────────────────────────────────────────
    "banned_message": {
        "ru": "⛔ Твой аккаунт заблокирован. Обратись к @admin если считаешь это ошибкой.",
        "uz": "⛔ Hisobingiz bloklangan. Xato deb hisoblasangiz @admin ga murojaat qiling.",
    },

    # ── Обращение в поддержку ───────────────────────────────────────────────
    "complaint_start": {
        "ru": "🛡 <b>Обращение в поддержку</b>\n\nНапишите сообщение или отправьте скриншот.",
        "uz": "🛡 <b>Yordam markazi</b>\n\nXabaringizni yoki screenshot yuboring.",
    },
    "complaint_sent": {
        "ru": "✅ <b>Отправлено!</b>\n\nМы скоро рассмотрим 🙏",
        "uz": "✅ <b>Yuborildi!</b>\n\nTez orada ko'rib chiqamiz 🙏",
    },
    "cancel": {
        "ru": "❌ Отмена",
        "uz": "❌ Bekor qilish",
    },

    # ── Мэтчи ───────────────────────────────────────────────────────────────
    "no_matches": {
        "ru": "😔 У тебя пока нет мэтчей\n\nСмотри анкеты и ставь лайки!",
        "uz": "😔 Hali mos kelganlar yo'q\n\nProfil ko'rib layk bos!",
    },
    "matches_title": {
        "ru": "💌 <b>Твои мэтчи:</b>",
        "uz": "💌 <b>Sizning mos kelganlaringiz:</b>",
    },
    "match_item": {
        "ru": "• {name}, {age} — {city}",
        "uz": "• {name}, {age} — {city}",
    },
    "write_to": {
        "ru": "✉️ Написать {name}",
        "uz": "✉️ Yozish {name}",
    },
    "no_username": {
        "ru": "❌ Нет username",
        "uz": "❌ Username yo'q",
    },
}


def t(key: str, lang: str = "ru", **kwargs) -> str:
    """
    Получить текст по ключу и языку.
    Поддерживает форматирование: t("reg_done", lang, name="Алишер")
    """
    entry = TEXTS.get(key)
    if entry is None:
        return f"[MISSING: {key}]"

    # Если значение — список (например report_reasons) — вернуть список
    if isinstance(entry.get("ru"), list):
        return entry.get(lang, entry.get("ru"))

    text = entry.get(lang) or entry.get("ru") or f"[MISSING: {key}]"
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text  # ✅ Убрана лишняя запятая