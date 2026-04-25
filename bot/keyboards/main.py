from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from bot.i18n import t


def main_menu_kb(lang: str = "ru") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [t("menu_browse", lang),    t("menu_search", lang)],
            [t("menu_favorites", lang), t("menu_referral", lang)],
        ],
        resize_keyboard=True,
    )


def language_kb() -> InlineKeyboardMarkup:
    ...  # остальное без изменений


def language_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang:ru"),
        InlineKeyboardButton("🇺🇿 O'zbek",  callback_data="lang:uz"),
    ]])


def gender_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(t("btn_male",   lang), callback_data="gender:male"),
        InlineKeyboardButton(t("btn_female", lang), callback_data="gender:female"),
    ]])


def looking_for_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(t("btn_looking_male",   lang), callback_data="looking:male"),
        InlineKeyboardButton(t("btn_looking_female", lang), callback_data="looking:female"),
        InlineKeyboardButton(t("btn_looking_all",    lang), callback_data="looking:all"),
    ]])


def tags_kb(all_tags: list, selected_ids: set, lang: str = "ru") -> InlineKeyboardMarkup:
    buttons, row = [], []
    for tag in all_tags:
        mark  = "✅ " if tag.id in selected_ids else ""
        label = (tag.name_uz if lang == "uz" and tag.name_uz else tag.name)
        row.append(InlineKeyboardButton(
            f"{mark}{tag.emoji or ''}{label}",
            callback_data=f"tag:{tag.id}"
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(t("btn_done", lang), callback_data="tags:done")])
    return InlineKeyboardMarkup(buttons)


def home_inline_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_home_browse",  lang), callback_data="home:browse"),
         InlineKeyboardButton(t("btn_home_profile", lang), callback_data="home:myprofile")],
        [InlineKeyboardButton(t("btn_home_hide",    lang), callback_data="home:stop"),
         InlineKeyboardButton(t("btn_home_premium", lang), callback_data="home:premium")],
    ])


def like_skip_kb(target_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(t("btn_like",         lang), callback_data=f"like:{target_id}"),
        InlineKeyboardButton(t("btn_fav",          lang), callback_data=f"fav:{target_id}"),
        InlineKeyboardButton(t("btn_skip_profile", lang), callback_data=f"skip:{target_id}"),
    ], [
        InlineKeyboardButton("🚨 Пожаловаться", callback_data=f"report:{target_id}"),
    ]])


def report_reason_kb(target_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    reasons = t("report_reasons", lang)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(r, callback_data=f"report_reason:{target_id}:{i}")]
        for i, r in enumerate(reasons)
    ])


def profile_actions_kb(lang: str = "ru", is_active: bool = True) -> InlineKeyboardMarkup:
    hide_label = (
        ("🙈 Скрыть" if lang == "ru" else "🙈 Yashirish") if is_active
        else ("👁 Показать" if lang == "ru" else "👁 Ko'rsatish")
    )
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_profile_edit",    lang), callback_data="profile:edit"),
         InlineKeyboardButton(t("btn_profile_photo",   lang), callback_data="profile:photo")],
        [InlineKeyboardButton(t("btn_profile_preview", lang), callback_data="profile:preview"),
         InlineKeyboardButton(hide_label,                      callback_data="profile:toggle")],
        [InlineKeyboardButton(t("btn_profile_delete",  lang), callback_data="profile:delete")],
    ])


def profile_edit_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_edit_name",    lang), callback_data="edit:name"),
         InlineKeyboardButton(t("btn_edit_age",     lang), callback_data="edit:age")],
        [InlineKeyboardButton(t("btn_edit_city",    lang), callback_data="edit:city"),
         InlineKeyboardButton(t("btn_edit_about",   lang), callback_data="edit:about")],
        [InlineKeyboardButton(t("btn_edit_tags",    lang), callback_data="edit:tags"),
         InlineKeyboardButton(t("btn_edit_looking", lang), callback_data="edit:looking")],
        [InlineKeyboardButton(t("btn_back",         lang), callback_data="profile:back")],
    ])


def profile_delete_confirm_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(t("btn_delete_yes", lang), callback_data="profile:delete_confirm"),
        InlineKeyboardButton(t("btn_delete_no",  lang), callback_data="profile:back"),
    ]])


# ── Избранное — кнопка "Написать" убрана, только удалить ─────────────────────
def favorites_item_kb(target_id: int, lang: str = "ru", has_vip: bool = False) -> InlineKeyboardMarkup:
    rows = []
    if has_vip:
        rows.append([InlineKeyboardButton(
            "💌 Запросить личку (VIP)" if lang == "ru" else "💌 Aloqa so'rash (VIP)",
            callback_data=f"vip_contact:{target_id}"
        )])
    rows.append([
        InlineKeyboardButton(
            "🗑 Удалить из избранного" if lang == "ru" else "🗑 Sevimlilardan o'chirish",
            callback_data=f"fav_remove:{target_id}"
        )
    ])
    return InlineKeyboardMarkup(rows)


def favorites_nav_kb(current: int, total: int) -> InlineKeyboardMarkup:
    row = []
    if current > 0:
        row.append(InlineKeyboardButton("◀️", callback_data=f"fav_nav:{current - 1}"))
    row.append(InlineKeyboardButton(f"{current + 1}/{total}", callback_data="fav_nav:noop"))
    if current < total - 1:
        row.append(InlineKeyboardButton("▶️", callback_data=f"fav_nav:{current + 1}"))
    return InlineKeyboardMarkup([row])


def referral_kb(bot_username: str, referral_code: str, lang: str = "ru") -> InlineKeyboardMarkup:
    link = f"https://t.me/{bot_username}?start=ref_{referral_code}"
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            t("btn_referral_share", lang),
            url=f"https://t.me/share/url?url={link}"
        ),
    ]])


CARD_NUMBER = "5614 6816 2116 5566"

PREMIUM_PLANS = {
    "1m": {
        "label": {"ru": "⭐ Premium — 1 месяц",  "uz": "⭐ Premium — 1 oy"},
        "price": {"ru": "30 000 сум",             "uz": "30 000 so'm"},
        "days":  30,
        "type":  "premium",
    },
    "3m": {
        "label": {"ru": "⭐ Premium — 3 месяца", "uz": "⭐ Premium — 3 oy"},
        "price": {"ru": "70 000 сум",             "uz": "70 000 so'm"},
        "days":  90,
        "type":  "premium",
    },
    "1y": {
        "label": {"ru": "⭐ Premium — 1 год",    "uz": "⭐ Premium — 1 yil"},
        "price": {"ru": "250 000 сум",            "uz": "250 000 so'm"},
        "days":  365,
        "type":  "premium",
    },
    "vip": {
        "label": {"ru": "💎 VIP Premium — 1 год", "uz": "💎 VIP Premium — 1 yil"},
        "price": {"ru": "3 000 000 сум",           "uz": "3 000 000 so'm"},
        "days":  365,
        "type":  "vip",
    },
}


def premium_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "⭐ Premium — 1 месяц  |  30 000 сум" if lang == "ru" else "⭐ Premium — 1 oy  |  30 000 so'm",
            callback_data="premium:1m"
        )],
        [InlineKeyboardButton(
            "⭐ Premium — 3 месяца  |  70 000 сум" if lang == "ru" else "⭐ Premium — 3 oy  |  70 000 so'm",
            callback_data="premium:3m"
        )],
        [InlineKeyboardButton(
            "⭐ Premium — 1 год  |  250 000 сум" if lang == "ru" else "⭐ Premium — 1 yil  |  250 000 so'm",
            callback_data="premium:1y"
        )],
        [InlineKeyboardButton(
            "💎 VIP Premium — 1 год  |  3 000 000 сум" if lang == "ru" else "💎 VIP Premium — 1 yil  |  3 000 000 so'm",
            callback_data="premium:vip"
        )],
    ])


def payment_confirm_kb(plan: str, lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(t("btn_pay_confirm", lang), callback_data=f"pay_confirm:{plan}"),
    ]])


def search_mode_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(t("btn_search_tag",  lang), callback_data="search:tag"),
        InlineKeyboardButton(t("btn_search_city", lang), callback_data="search:city"),
    ]])


def search_tags_kb(all_tags: list, lang: str = "ru") -> InlineKeyboardMarkup:
    buttons, row = [], []
    for tag in all_tags:
        label = (tag.name_uz if lang == "uz" and tag.name_uz else tag.name)
        row.append(InlineKeyboardButton(
            f"{tag.emoji or ''}{label}",
            callback_data=f"search_tag:{tag.id}"
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)