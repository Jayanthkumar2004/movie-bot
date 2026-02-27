import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ---------------- ENV VARIABLES ---------------- #
BOT_TOKEN = os.environ.get("8621751216:AAHJ9Nt4BR50hi2QkPGYhXtgQD9eWh5BnEM")
TMDB_API_KEY = os.environ.get("c6ccbca98ba165e9b6f9757611e23338")

BASE_URL = "https://api.themoviedb.org/3"


# ---------------- SEARCH MOVIE ---------------- #
def get_movie_data(movie_name):
    url = f"{BASE_URL}/search/movie"

    params = {
        "api_key": TMDB_API_KEY,
        "query": movie_name,
        "include_adult": False,
        "language": "en-US",
        "region": "IN"
    }

    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()

        if data.get("results"):
            return data["results"][0]

        return None

    except Exception as e:
        print("Search Error:", e)
        return None


# ---------------- MOVIE DETAILS ---------------- #
def get_movie_details(movie_id):
    url = f"{BASE_URL}/movie/{movie_id}"

    params = {
        "api_key": TMDB_API_KEY,
        "append_to_response": "videos"
    }

    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        return res.json()

    except Exception as e:
        print("Details Error:", e)
        return None


# ---------------- TRENDING MOVIES ---------------- #
def get_trending_movies():
    url = f"{BASE_URL}/trending/movie/day"

    params = {"api_key": TMDB_API_KEY}

    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        return data.get("results", [])[:5]

    except Exception as e:
        print("Trending Error:", e)
        return []


# ---------------- BUILD CAPTION ---------------- #
def build_caption(movie_data):
    title = movie_data.get("title", "Unknown")
    year = movie_data.get("release_date", "")[:4]
    rating = movie_data.get("vote_average", "N/A")
    overview = movie_data.get("overview", "No description available.")
    language = movie_data.get("original_language", "").upper()
    popularity = round(movie_data.get("popularity", 0), 1)

    caption = f"""
<b>🎬 {title} ({year})</b>

⭐ <b>Rating:</b> {rating}/10
🌍 <b>Language:</b> {language}
🔥 <b>Popularity:</b> {popularity}

━━━━━━━━━━━━━━━

<b>📖 Description</b>

{overview[:350]}...

━━━━━━━━━━━━━━━
"""
    return caption


# ---------------- START COMMAND ---------------- #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Movie Bot is Live!\n\n"
        "Use:\n"
        "/movie movie_name\n"
        "/trending"
    )


# ---------------- MOVIE COMMAND ---------------- #
async def movie(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Use: /movie movie_name")
        return

    movie_name = " ".join(context.args)

    data = get_movie_data(movie_name)
    if not data:
        await update.message.reply_text("❌ Movie not found.")
        return

    details = get_movie_details(data["id"])
    if not details:
        await update.message.reply_text("❌ Could not fetch movie details.")
        return

    caption = build_caption(details)

    poster_path = details.get("poster_path")
    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

    imdb_id = details.get("imdb_id")
    imdb_url = f"https://www.imdb.com/title/{imdb_id}" if imdb_id else None

    trailer_url = None
    videos = details.get("videos", {}).get("results", [])
    for video in videos:
        if video.get("type") == "Trailer" and video.get("site") == "YouTube":
            trailer_url = f"https://www.youtube.com/watch?v={video.get('key')}"
            break

    buttons = []
    if imdb_url:
        buttons.append([InlineKeyboardButton("🎬 View on IMDb", url=imdb_url)])

    if trailer_url:
        buttons.append([InlineKeyboardButton("🎥 Watch Trailer", url=trailer_url)])

    reply_markup = InlineKeyboardMarkup(buttons) if buttons else None

    if poster_url:
        await update.message.reply_photo(
            photo=poster_url,
            caption=caption,
            parse_mode="HTML",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            caption,
            parse_mode="HTML",
            reply_markup=reply_markup
        )


# ---------------- TRENDING COMMAND ---------------- #
async def trending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    movies = get_trending_movies()

    if not movies:
        await update.message.reply_text("❌ Could not fetch trending movies.")
        return

    message = "🔥 <b>Trending Movies Today</b>\n\n"

    for i, movie in enumerate(movies, 1):
        title = movie.get("title")
        rating = movie.get("vote_average")
        message += f"{i}. {title} ⭐ {rating}\n"

    await update.message.reply_text(message, parse_mode="HTML")


# ---------------- MAIN ---------------- #
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("movie", movie))
    app.add_handler(CommandHandler("trending", trending))

    print("Bot running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()