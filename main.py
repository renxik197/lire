from flask import Flask, render_template, render_template_string, request, session, redirect, url_for
import pandas as pd
import os
import random
import re
import ssl
import urllib.parse
import urllib.request
import json

app = Flask(__name__)
app.secret_key = "lire_secret_key_2026"


# ======================
# ЗАГРУЗКА СЛОВАРЯ
# ======================
def load_dictionary():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "database", "idioms_database.xlsx")
    data = pd.read_excel(path)
    data = data.fillna("")
    return data


df = load_dictionary()

# ======================
# ТЕКСТЫ ИНТЕРФЕЙСА
# ======================

TEXTS = {
    "ru": {
        "site_title": "LiRe",
        "tagline": "Learning Idioms Right Easily",
        "welcome": "Добро пожаловать на сайт для изучения устойчивых выражений английского языка!",
        "home": "Главная",
        "dictionary": "Словарь",
        "translator": "Переводчик",
        "cards": "Карточки",
        "texts": "Советы",
        "search_placeholder": "Введите идиому или слово...",
        "search_btn": "Искать",
        "category": "Категория",
        "all_categories": "Все категории",
        "phrase": "Фраза",
        "literal": "Дословный перевод",
        "figurative": "Переносное значение",
        "origin": "Происхождение",
        "example": "Примеры",
        "synonyms": "Синонимы",
        "no_results": "Ничего не найдено",
        "found": "Найдено",
        "random_idiom": "Случайная идиома",
        "translate": "Перевести",
        "enter_text": "Введите текст для перевода",
        "from_lang": "С языка",
        "to_lang": "На язык",
        "result": "Результат",
        "back": "Назад",
        "module_dict_title": "Словарь",
        "module_dict_desc": "Здесь можно найти значение новых слов и выражений.",
        "module_trans_title": "Переводчик",
        "module_trans_desc": "Быстро переводи идиомы и смотри их значения.",
        "module_cards_title": "Карточки Memory",
        "module_cards_desc": "Повтори изученные идиомы или выучи новые.",
        "module_texts_title": "Советы",
        "module_texts_desc": "Рекомендации, которые помогут учить идиомы эффективнее.",
        "memory_title": "Карточки Memory",
        "train": "Тренировка",
        "train_desc": "Выбери верный перевод",
        "truefalse": "Правда или Ложь",
        "truefalse_desc": "Определи правдивость определения",
        "random_card": "Случайная идиома",
        "random_card_desc": "Открыть случайную карточку",
        "true_btn": "Правда",
        "false_btn": "Ложь",
        "next": "Дальше",
        "correct": "Верно!",
        "incorrect": "Неверно",
        "texts_soon": "Раздел советов",
        "open": "Открыть",
    },
    "en": {
        "site_title": "LiRe",
        "tagline": "Learning Idioms Right Easily",
        "welcome": "Welcome to the site for learning English idioms and fixed expressions!",
        "home": "Home",
        "dictionary": "Dictionary",
        "translator": "Translator",
        "cards": "Cards",
        "texts": "Tips",
        "search_placeholder": "Enter an idiom or word...",
        "search_btn": "Search",
        "category": "Category",
        "all_categories": "All categories",
        "phrase": "Phrase",
        "literal": "Literal translation",
        "figurative": "Figurative meaning",
        "origin": "Origin",
        "example": "Examples",
        "synonyms": "Synonyms",
        "no_results": "No results found",
        "found": "Found",
        "random_idiom": "Random idiom",
        "translate": "Translate",
        "enter_text": "Enter text to translate",
        "from_lang": "From",
        "to_lang": "To",
        "result": "Result",
        "back": "Back",
        "module_dict_title": "Dictionary",
        "module_dict_desc": "Find meanings of new words and expressions.",
        "module_trans_title": "Translator",
        "module_trans_desc": "Quickly translate idioms and see their meanings.",
        "module_cards_title": "Memory Cards",
        "module_cards_desc": "Review learned idioms or learn new ones.",
        "module_texts_title": "Tips",
        "module_texts_desc": "Recommendations to help you learn idioms more effectively.",
        "memory_title": "Memory Cards",
        "train": "Practice",
        "train_desc": "Choose the correct translation",
        "truefalse": "True or False",
        "truefalse_desc": "Decide if the definition is true",
        "random_card": "Random idiom",
        "random_card_desc": "Open a random card",
        "true_btn": "True",
        "false_btn": "False",
        "next": "Next",
        "correct": "Correct!",
        "incorrect": "Incorrect",
        "texts_soon": "Tips section",
        "open": "Open",
    }
}



def t():
    lang = session.get("lang", "ru")
    return TEXTS.get(lang, TEXTS["ru"])


# ======================
# СМЕНА ЯЗЫКА
# ======================
@app.route("/set_lang/<lang>")
def set_lang(lang):
    if lang in ["ru", "en"]:
        session["lang"] = lang
    return redirect(request.referrer or url_for("home"))


# ======================
# ГЛАВНАЯ
# ======================
@app.route("/")
def home():
    return render_template("index.html", t=t(), lang=session.get("lang", "ru"))
 

# ======================
# СЛОВАРЬ
# ======================
@app.route("/dictionary")
def dictionary():
    query = request.args.get("q", "").strip().lower()
    category = request.args.get("category", "all")

    data = df.copy()

    if query:
        data = data[
            data["phrase"].astype(str).str.lower().str.contains(query, na=False) |
            data["literal_ru"].astype(str).str.lower().str.contains(query, na=False) |
            data["figurative_ru"].astype(str).str.lower().str.contains(query, na=False)
        ]

    if category != "all":
        data = data[data["category"] == category]

    categories = sorted([c for c in df["category"].dropna().unique().tolist() if c])

    return render_template(
        "dictionary.html",
        t=t(),
        lang=session.get("lang", "ru"),
        idioms=data.to_dict(orient="records"),
        categories=categories,
        query=request.args.get("q", ""),
        selected_category=category
    )


# ======================
# КАРТОЧКА ОДНОЙ ИДИОМЫ
# ======================
@app.route("/idiom/<idiom_id>")
def idiom_page(idiom_id):
    row = df[df["id"].astype(str) == str(idiom_id)]
    if row.empty:
        return "Idiom not found", 404

    idiom = row.iloc[0].to_dict()
    examples = [e.strip() for e in str(idiom.get("examples_en", "")).split("|") if e.strip()]

    return render_template(
        "idiom.html",
        t=t(),
        lang=session.get("lang", "ru"),
        idiom=idiom,
        examples=examples
    )


# ======================
# СЛУЧАЙНАЯ ИДИОМА
# ======================
@app.route("/random")
def random_idiom():
    row = df.sample(1).iloc[0]
    return redirect(url_for("idiom_page", idiom_id=row["id"]))


# ======================
# ПЕРЕВОДЧИК
# ======================
@app.route("/translator", methods=["GET", "POST"])
def translator():
    result = None
    original = ""
    error = ""

    if request.method == "POST":
        original = request.form.get("text", "").strip()

        if not original:
            error = "Введите идиому"
        else:
            q = original.lower()
            found = df[df["phrase"].astype(str).str.lower().str.contains(q, na=False)]

            if not found.empty:
                row = found.iloc[0]
                result = {
                    "phrase": str(row.get("phrase", "")),
                    "category": str(row.get("category", "")),
                    "literal_ru": str(row.get("literal_ru", "")),
                    "figurative_ru": str(row.get("figurative_ru", "")),
                    "origin_ru": str(row.get("origin_ru", "")),
                    "synonyms": str(row.get("synonyms", "")),
                    "examples": str(row.get("examples_en", "")),
                }
            else:
                error = "Идиома не найдена в базе"

    return render_template(
        "translator.html",
        t=t(),
        lang=session.get("lang", "ru"),
        result=result,
        original=original,
        error=error
    )

# ======================
# MEMORY — МЕНЮ
# ======================
@app.route("/memory")
def memory():
    return render_template("memory.html", t=t(), lang=session.get("lang", "ru"))


# ======================
# MEMORY — ТРЕНИРОВКА
# ======================
@app.route("/memory/train")
def memory_train():
    correct = df.sample(1).iloc[0]
    wrongs = df[df["id"] != correct["id"]].sample(3)
    options = [correct["figurative_ru"]] + wrongs["figurative_ru"].tolist()
    random.shuffle(options)

    return render_template(
        "memory_train.html",
        t=t(),
        lang=session.get("lang", "ru"),
        phrase=correct["phrase"],
        correct=correct["figurative_ru"],
        options=options,
        idiom_id=correct["id"]
    )


# ======================
# MEMORY — ПРАВДА / ЛОЖЬ
# ======================
@app.route("/memory/truefalse")
def memory_truefalse():
    row = df.sample(1).iloc[0]
    is_true = random.choice([True, False])

    if is_true:
        shown_meaning = str(row["figurative_ru"])
    else:
        other = df[df["id"] != row["id"]].sample(1).iloc[0]
        shown_meaning = str(other["figurative_ru"])

    return render_template(
        "memory_truefalse.html",
        t=t(),
        lang=session.get("lang", "ru"),
        phrase=str(row["phrase"]),
        meaning=shown_meaning,
        is_true=is_true
    )


# ======================
# СОВЕТЫ - СПИСОК
# ======================
@app.route("/texts")
def texts():
    tips = [
        {
            "title_ru": "Учи идиомы в контексте",
            "title_en": "Learn idioms in context",
            "text_ru": "Не заучивай список просто так. Читай короткие диалоги, смотри сериалы и отмечай, в какой ситуации звучит выражение.",
            "text_en": "Do not just memorize a list. Read short dialogues, watch series, and notice in what situation the expression is used."
        },
        {
            "title_ru": "Повторяй через карточки",
            "title_en": "Review with flashcards",
            "text_ru": "Раздел Memory помогает закрепить значение. Лучше по 5–10 идиом в день, чем 50 за один раз и забыть.",
            "text_en": "The Memory section helps you remember meanings. Better 5–10 idioms a day than 50 at once and then forgetting them."
        },
        {
            "title_ru": "Сравнивай дословный и переносный смысл",
            "title_en": "Compare literal and figurative meaning",
            "text_ru": "Дословный перевод часто звучит странно. Именно поэтому важно смотреть переносное значение и примеры.",
            "text_en": "A literal translation often sounds strange. That is why the figurative meaning and examples are so important."
        },
        {
            "title_ru": "Говори вслух",
            "title_en": "Say it out loud",
            "text_ru": "Произнеси идиому и пример предложения вслух. Так лучше запоминается и легче потом использовать в речи.",
            "text_en": "Say the idiom and an example sentence out loud. This helps memory and makes it easier to use later in speech."
        },
        {
            "title_ru": "Веди свой мини-список",
            "title_en": "Keep a mini list",
            "text_ru": "Выписывай 3–5 новых выражений в неделю и возвращайся к ним через 2–3 дня.",
            "text_en": "Write down 3–5 new expressions a week and come back to them after 2–3 days."
        },
        {
            "title_ru": "Не бойся ошибок",
            "title_en": "Do not fear mistakes",
            "text_ru": "Даже носители иногда путают устойчивые выражения. Главное — понимать смысл и постепенно набирать опыт.",
            "text_en": "Even native speakers sometimes mix up fixed expressions. The main thing is to understand the meaning and gain experience step by step."
        },
        {
            "title_ru": "Связывай с русскими аналогами",
            "title_en": "Connect with Russian equivalents",
            "text_ru": "Иногда помогает найти похожий фразеологизм на русском. Так значение запоминается быстрее.",
            "text_en": "Sometimes it helps to find a similar phrase in Russian. This way the meaning is remembered faster."
        },
        {
            "title_ru": "Используй сайт по кругу",
            "title_en": "Use the site in a loop",
            "text_ru": "Схема простая: нашли идиому в словаре → посмотрели примеры → проверилт себя в карточках Memory.",
            "text_en": "A simple loop: find an idiom in the dictionary → look at examples → check yourself in Memory cards."
        },
    ]

    return render_template(
        "texts.html",
        t=t(),
        lang=session.get("lang", "ru"),
        tips=tips
    )

        
# ======================
# ЗАПУСК
# ======================
if __name__ == "__main__":
    app.run(debug=True)