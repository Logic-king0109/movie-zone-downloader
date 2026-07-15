import os
import re
import asyncio
import requests
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from difflib import get_close_matches
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from dotenv import load_dotenv

# ============================================
# SETUP
# ============================================

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
DOWNLOAD_PATH = './downloads'

if not BOT_TOKEN:
    print('❌ Please set BOT_TOKEN in .env file!')
    exit(1)

os.makedirs(DOWNLOAD_PATH, exist_ok=True)
sessions = {}
active_downloads = {}
download_pool = ThreadPoolExecutor(max_workers=10)

BOT_PHOTO_URL = "mylogo.png"

FORCE_JOIN_CHANNEL = '@LogicKingNetwork'
FORCE_JOIN_URL = 'https://t.me/LogicKingNetwork'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

SEARCH_EMOJIS = ['🔍','📡','🌐','💻','🎯','✨','⚡','🎬']
DOWNLOAD_EMOJIS = ['📥','💾','⚡','📦','🚀','🎯','💫','✨','🔥','📊']
PROGRESS_BARS = ['▱▱▱▱▱▱▱▱▱▱','▰▱▱▱▱▱▱▱▱▱','▰▰▱▱▱▱▱▱▱▱','▰▰▰▱▱▱▱▱▱▱','▰▰▰▰▱▱▱▱▱▱','▰▰▰▰▰▱▱▱▱▱','▰▰▰▰▰▰▱▱▱▱','▰▰▰▰▰▰▰▱▱▱','▰▰▰▰▰▰▰▰▱▱','▰▰▰▰▰▰▰▰▰▱','▰▰▰▰▰▰▰▰▰▰']

COMMON_MOVIES = [
    'iron man', 'iron man 2', 'iron man 3', 'thor', 'thor the dark world', 'thor ragnarok', 'thor love and thunder',
    'captain america', 'captain america winter soldier', 'captain america civil war',
    'avengers', 'avengers age of ultron', 'avengers infinity war', 'avengers endgame',
    'guardians of the galaxy', 'guardians of the galaxy vol 2', 'guardians of the galaxy vol 3',
    'ant man', 'ant man and the wasp', 'ant man quantumania',
    'doctor strange', 'doctor strange multiverse of madness',
    'spider man homecoming', 'spider man far from home', 'spider man no way home',
    'black panther', 'black panther wakanda forever',
    'captain marvel', 'the marvels', 'black widow', 'shang chi', 'eternals',
    'deadpool', 'deadpool 2', 'deadpool and wolverine', 'venom', 'venom let there be carnage', 'venom the last dance',
    'x men', 'x men 2', 'x men the last stand', 'x men first class', 'x men days of future past', 'x men apocalypse', 'x men dark phoenix',
    'wolverine', 'the wolverine', 'logan',
    'superman', 'superman 2', 'superman returns', 'man of steel',
    'batman', 'batman begins', 'the dark knight', 'the dark knight rises', 'the batman',
    'wonder woman', 'wonder woman 1984', 'aquaman', 'the flash',
    'justice league', 'suicide squad', 'the suicide squad', 'joker',
    'avatar', 'avatar the way of water', 'avatar fire and ash',
    'star wars', 'the empire strikes back', 'return of the jedi', 'the phantom menace', 'attack of the clones', 'revenge of the sith',
    'the force awakens', 'the last jedi', 'the rise of skywalker', 'rogue one',
    'harry potter', 'chamber of secrets', 'prisoner of azkaban', 'goblet of fire', 'order of the phoenix', 'half blood prince', 'deathly hallows',
    'lord of the rings', 'the fellowship of the ring', 'the two towers', 'the return of the king',
    'the hobbit', 'the desolation of smaug', 'the battle of the five armies',
    'jurassic park', 'the lost world', 'jurassic park 3', 'jurassic world', 'fallen kingdom', 'dominion', 'jurassic world rebirth',
    'fast and furious', '2 fast 2 furious', 'tokyo drift', 'fast five', 'fast and furious 6', 'furious 7', 'fast x',
    'mission impossible', 'mission impossible 2', 'mission impossible 3', 'ghost protocol', 'rogue nation', 'fallout', 'dead reckoning',
    'transformers', 'revenge of the fallen', 'dark of the moon', 'age of extinction', 'the last knight', 'bumblebee', 'rise of the beasts',
    'pirates of the caribbean', 'dead mans chest', 'at worlds end', 'on stranger tides',
    'terminator', 'terminator 2', 'terminator 3', 'terminator salvation', 'terminator genisys', 'terminator dark fate',
    'alien', 'aliens', 'alien 3', 'prometheus', 'alien covenant', 'alien romulus',
    'predator', 'predator 2', 'predators', 'the predator', 'prey',
    'john wick', 'john wick 2', 'john wick 3', 'john wick 4',
    'the matrix', 'the matrix reloaded', 'the matrix revolutions', 'the matrix resurrections',
    'inception', 'interstellar', 'tenet', 'dunkirk', 'oppenheimer',
    'the conjuring', 'the conjuring 2', 'the conjuring 3', 'the nun', 'the nun 2',
    'insidious', 'insidious 2', 'insidious 3', 'insidious the red door',
    'it', 'it chapter two', 'a quiet place', 'a quiet place 2', 'a quiet place day one',
    'get out', 'us', 'nope', 'halloween', 'scream', 'scream 6',
    'saw', 'saw x', 'the ring', 'the grudge', 'the exorcist',
    'die hard', 'die hard 2', 'die hard with a vengeance', 'live free or die hard',
    'mad max', 'mad max fury road', 'furiosa',
    'rambo', 'rambo first blood', 'rambo last blood',
    'the expendables', 'the expendables 2', 'the expendables 3', 'the expendables 4',
    'bad boys', 'bad boys 2', 'bad boys for life', 'bad boys ride or die',
    'rush hour', 'rush hour 2', 'rush hour 3', 'taken', 'taken 2', 'taken 3',
    'the equalizer', 'the equalizer 2', 'the equalizer 3',
    'top gun', 'top gun maverick', 'gladiator', 'gladiator 2',
    '300', '300 rise of an empire', 'troy',
    'dune', 'dune part two', 'blade runner', 'blade runner 2049',
    'the martian', 'gravity', 'district 9', 'edge of tomorrow',
    'pacific rim', 'pacific rim uprising', 'godzilla', 'godzilla vs kong', 'godzilla x kong',
    'ready player one', 'free guy',
    'toy story', 'toy story 2', 'toy story 3', 'toy story 4',
    'finding nemo', 'finding dory', 'the incredibles', 'the incredibles 2',
    'frozen', 'frozen 2', 'moana', 'moana 2', 'encanto',
    'shrek', 'shrek 2', 'shrek 3', 'shrek forever after', 'puss in boots the last wish',
    'how to train your dragon', 'how to train your dragon 2', 'how to train your dragon 3',
    'kung fu panda', 'kung fu panda 2', 'kung fu panda 3', 'kung fu panda 4',
    'despicable me', 'despicable me 2', 'despicable me 3', 'despicable me 4',
    'minions', 'the super mario bros movie', 'sonic the hedgehog', 'sonic 2', 'sonic 3',
    'spider man into the spider verse', 'spider man across the spider verse',
    'the shawshank redemption', 'the godfather', 'the godfather 2',
    'forrest gump', 'fight club', 'goodfellas', 'the departed',
    'parasite', 'slumdog millionaire',
    'game of thrones', 'house of the dragon', 'breaking bad', 'better call saul',
    'stranger things', 'the walking dead', 'vikings', 'vikings valhalla',
    'peaky blinders', 'ozark', 'narcos', 'the witcher', 'the mandalorian',
    'the boys', 'invincible', 'squid game', 'wednesday', 'the last of us',
    'attack on titan', 'demon slayer', 'jujutsu kaisen', 'chainsaw man',
    'one piece', 'naruto', 'dragon ball z', 'dragon ball super',
    'my hero academia', 'death note', 'one punch man', 'solo leveling',
    'the wedding party', 'king of boys', 'omo ghetto', 'anikulapo',
    'dangal', 'rrr', 'baahubali', '3 idiots', 'pathaan', 'jawan',
    'atlas', 'war machine', 'mortal kombat',
]

def auto_correct(query):
    query_lower = query.lower().strip()
    query_lower = re.sub(r'[^\w\s]', '', query_lower)
    query_lower = re.sub(r'\s+', ' ', query_lower).strip()
    
    typo_fixes = {
        'spiderman': 'spider man', 'avangers': 'avengers', 'jrassic': 'jurassic',
        'john wic': 'john wick', 'dead pool': 'deadpool', 'intersteller': 'interstellar',
        'terminater': 'terminator', 'transformars': 'transformers',
        'stranger thing': 'stranger things', 'game of throne': 'game of thrones',
        'braking bad': 'breaking bad', 'peaky blinder': 'peaky blinders',
        'wicher': 'the witcher', 'walking dead': 'the walking dead', 'last of us': 'the last of us',
    }
    
    if query_lower in typo_fixes:
        return typo_fixes[query_lower]
    
    matches = get_close_matches(query_lower, COMMON_MOVIES, n=1, cutoff=0.6)
    if matches and matches[0] != query_lower:
        return matches[0]
    
    return query

async def check_subscription(user_id, context):
    try:
        member = await context.bot.get_chat_member(FORCE_JOIN_CHANNEL, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except:
        return True

async def require_subscription(update, context):
    user_id = update.effective_user.id
    if await check_subscription(user_id, context):
        return True
    
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=FORCE_JOIN_URL)],
        [InlineKeyboardButton("✅ I've Joined", callback_data='check_join')]
    ]
    
    await update.message.reply_text(
        f"⚠️ SUBSCRIPTION REQUIRED\n\n"
        f"📢 Join {FORCE_JOIN_CHANNEL} to use this bot!\n\n"
        f"1️⃣ Click 'Join Channel'\n2️⃣ Join the channel\n3️⃣ Click 'I've Joined'\n\n"
        f"👑 @Sir_logicking",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return False

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')
    def log_message(self, format, *args):
        pass

def start_health_server():
    port = int(os.environ.get('PORT', 10000))
    HTTPServer(('0.0.0.0', port), HealthHandler).serve_forever()

def cleanup_old_files():
    try:
        now = time.time()
        for filename in os.listdir(DOWNLOAD_PATH):
            filepath = os.path.join(DOWNLOAD_PATH, filename)
            if os.path.isfile(filepath):
                if now - os.path.getmtime(filepath) > 30:
                    try: os.remove(filepath)
                    except: pass
    except: pass

def cleanup_after_send(filepath):
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except: pass

class RobustDownloader:
    
    @staticmethod
    def selenium_get_link(dw_url):
        print(f'🖥️ Processing...')
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.by import By
            from webdriver_manager.chrome import ChromeDriverManager
            
            options = Options()
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--ignore-certificate-errors')
            
            try:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
            except:
                driver = webdriver.Chrome(options=options)
            
            driver.get(dw_url); time.sleep(5)
            direct_link = None
            
            try:
                form = driver.find_element(By.NAME, 'F1')
                form.submit(); time.sleep(8)
                page = driver.page_source
                found = re.findall(r'https?://\w+\.downloadwella\.com/d/[^\s"\'<>]+\.mkv', page)
                if found: direct_link = found[0]
            except: pass
            
            if not direct_link:
                try:
                    btn = driver.find_element(By.ID, 'downloadbtn')
                    driver.execute_script("arguments[0].click();", btn)
                    for _ in range(3):
                        time.sleep(5)
                        found = re.findall(r'https?://\w+\.downloadwella\.com/d/[^\s"\'<>]+\.mkv', driver.page_source)
                        if found: direct_link = found[0]; break
                except: pass
            
            if not direct_link:
                found = re.findall(r'https?://\w+\.downloadwella\.com/d/[^\s"\'<>]+\.mkv', driver.page_source)
                if found: direct_link = found[0]
            
            driver.quit()
            return direct_link
        except Exception as e:
            print(f'❌ Selenium: {e}')
            return None
    
    @staticmethod
    def requests_get_link(dw_url):
        try:
            session = requests.Session()
            resp = session.get(dw_url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            form = soup.find('form', attrs={'name': 'F1'})
            if form:
                data = {}
                for inp in form.find_all('input'):
                    n = inp.get('name'); v = inp.get('value', '')
                    if n: data[n] = v
                if data.get('op') == 'download2':
                    resp2 = session.post(dw_url, data=data, headers=HEADERS, timeout=15)
                    found = re.findall(r'https?://\w+\.downloadwella\.com/d/[^\s"\'<>]+\.mkv', resp2.text)
                    if found: return found[0]
            found = re.findall(r'https?://\w+\.downloadwella\.com/d/[^\s"\'<>]+\.mkv', resp.text)
            return found[0] if found else None
        except:
            return None
    
    @staticmethod
    def download_file(url, progress_callback=None):
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        filename = url.split('/')[-1].split('?')[0]
        if not filename.endswith('.mkv'): filename += '.mkv'
        filepath = os.path.join(DOWNLOAD_PATH, filename)
        
        for attempt in range(20):
            try:
                resp = requests.get(url, headers=HEADERS, stream=True, timeout=600, verify=False)
                total = int(resp.headers.get('content-length', 0))
                with open(filepath, 'wb') as f:
                    downloaded = 0; last_update = 0
                    for chunk in resp.iter_content(chunk_size=16384):
                        if chunk:
                            f.write(chunk); downloaded += len(chunk)
                            if progress_callback and total > 0:
                                pct = int((downloaded/total)*100)
                                if pct >= last_update + 5:
                                    last_update = pct
                                    try: progress_callback(pct, downloaded, total)
                                    except: pass
                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    size = os.path.getsize(filepath)
                    if total == 0 or size >= total * 0.9: return filepath
                    else: os.remove(filepath)
            except Exception as e:
                print(f'❌ Attempt {attempt+1}: {e}')
                time.sleep(5)
        return None

downloader = RobustDownloader()

class ThenkiriScraper:
    SEARCH_URL = "https://thenkiri.com/?s={query}&post_type=post"
    
    def search(self, query):
        url = self.SEARCH_URL.format(query=query.replace(' ', '+'))
        print(f'🔍 {url}')
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            movies = []
            for article in soup.find_all('article'):
                link = article.find('a', href=True)
                title_elem = article.find(['h2', 'h3'])
                if link and title_elem:
                    href = link['href']; title = title_elem.get_text(strip=True)
                    if 'thenkiri.com' in href and '/category/' not in href:
                        img = article.find('img')
                        poster = img.get('src') if img else None
                        movies.append({'title': title[:100], 'url': href, 'poster': poster})
            if not movies:
                for link in soup.find_all('a', href=True):
                    h = link['href']; t = link.get_text(strip=True)
                    if 'thenkiri.com' in h and '/category/' not in h and len(t) > 10:
                        movies.append({'title': t[:100], 'url': h, 'poster': None})
            seen = set(); unique = []
            for m in movies:
                if m['url'] not in seen: seen.add(m['url']); unique.append(m)
            return unique[:15]
        except Exception as e:
            print(f'❌ {e}')
            return []
    
    def get_movie_info(self, url):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            title = "Unknown"
            t = soup.find('h1') or soup.find('h2')
            if t: title = t.get_text(strip=True)[:100]
            poster = None
            og = soup.find('meta', property='og:image')
            if og: poster = og.get('content')
            if not poster:
                img = soup.find('img')
                if img: poster = img.get('src')
            dw = None
            for link in soup.find_all('a', class_='elementor-button-link'):
                h = link.get('href','')
                if 'downloadwella.com' in h: dw = h; break
            if not dw:
                for link in soup.find_all('a', href=True):
                    if 'downloadwella.com' in link['href']: dw = link['href']; break
            if not dw:
                found = re.findall(r'https?://downloadwella\.com/[a-zA-Z0-9]+/[^\s"\'<>]+\.html', resp.text)
                if found: dw = found[0]
            return {'title': title, 'poster': poster, 'downloadwella_url': dw}
        except:
            return None

scraper = ThenkiriScraper()

async def start(update, context):
    user_name = update.effective_user.first_name
    
    keyboard = [
        [InlineKeyboardButton("📖 How to Use", callback_data='how_to_use')],
        [InlineKeyboardButton("🔍 Search Tips", callback_data='search_tips')],
        [InlineKeyboardButton("📢 Join Channel", url=FORCE_JOIN_URL)],
        [InlineKeyboardButton("👑 Developer", url='https://t.me/Sir_logicking')],
    ]
    
    caption = (
        f"👑 Welcome, {user_name}!\n\n"
        f"🎥 YOUR PREMIUM MOVIE EXPERIENCE\n\n"
        f"🔥 POWER FEATURES:\n"
        f"   ▸ 🔍 Smart Search + Auto-Correction\n"
        f"   ▸ 📥 10 Simultaneous Downloads\n"
        f"   ▸ ⚡ Lightning Fast Processing\n"
        f"   ▸ 🎨 Live Animated Progress\n"
        f"   ▸ 📊 Real-Time Size Tracking\n\n"
        f"🎬 WHAT YOU GET:\n"
        f"   ▸ 🎥 Hollywood Blockbusters\n"
        f"   ▸ 🇳🇬 Nollywood Hits\n"
        f"   ▸ 📺 TV Series (All Seasons)\n"
        f"   ▸ 🎌 Anime Collection\n"
        f"   ▸ 🇮🇳 Bollywood Movies\n\n"
        f"💎 PREMIUM QUALITY:\n"
        f"   ▸ HD 720p / Full HD 1080p\n"
        f"   ▸ MKV Format\n"
        f"   ▸ Fast Direct Downloads\n\n"
        f"🚀 Ready to download?\n"
        f"   Just type any movie name!\n\n"
        f"💡 Try: avatar, avengers, jurassic world\n\n"
        f"👑 Powered by: @Sir_logicking\n\n"
        f"⭐ You deserve the BEST!"
    )
    
    try:
        await update.message.reply_photo(photo=BOT_PHOTO_URL, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))
    except:
        await update.message.reply_text(caption, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_message(update, context):
    if not await require_subscription(update, context):
        return
    
    q = update.message.text; uid = update.effective_user.id
    
    corrected = auto_correct(q)
    if corrected != q.lower():
        await update.message.reply_text(f'🔍 Did you mean: {corrected.title()}?\nSearching...')
        q = corrected
    
    msg = await update.message.reply_text('🔍 Searching...')
    
    e_i = 0
    async def animate():
        nonlocal e_i
        while True:
            try:
                await msg.edit_text(f'{SEARCH_EMOJIS[e_i]} Searching "{q}"...')
                e_i = (e_i+1) % len(SEARCH_EMOJIS)
                await asyncio.sleep(0.5)
            except: break
    
    anim = asyncio.create_task(animate())
    
    try:
        loop = asyncio.get_event_loop()
        movies = await loop.run_in_executor(None, scraper.search, q)
        anim.cancel()
        
        if not movies:
            await msg.edit_text(f'❌ No movies found for "{q}"\n\nTry a different name.\n👑 @Sir_logicking')
            return
        
        sessions[uid] = {'movies': movies, 'page': 0, 'query': q}
        await show_movie(msg, uid)
    except Exception as e:
        anim.cancel()
        try: await msg.edit_text(f'❌ {str(e)[:100]}')
        except: pass
async def show_movie(msg, uid):
    s = sessions.get(uid)
    if not s: return
    movies = s['movies']; page = s['page']; total = len(movies)
    if page >= total: page = 0; s['page'] = 0
    movie = movies[page]
    
    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(None, scraper.get_movie_info, movie['url'])
    movie['info'] = info
    
    kb = []
    
    # ✅ Determine if this movie is valid (has a download link)
    has_movie = info and info.get('downloadwella_url')
    
    # 🔒 Only build navigation buttons if movie is valid
    nav = []
    if has_movie:
        if page > 0:
            nav.append(InlineKeyboardButton("⏮ First", callback_data='first'))
            nav.append(InlineKeyboardButton("⬅️ Prev", callback_data='prev'))
        if page < total-1:
            nav.append(InlineKeyboardButton("Next ➡️", callback_data='next'))
            nav.append(InlineKeyboardButton("Last ⏭", callback_data='last'))
    if nav:
        kb.append(nav)
    
    kb.append([InlineKeyboardButton("⏹ Stop", callback_data='stop_search'), 
               InlineKeyboardButton("▶️ Continue", callback_data='continue_search')])
    kb.append([InlineKeyboardButton(f"📄 {page+1} of {total}", callback_data='noop')])
    
    # ✅ Only show download button if movie exists
    if has_movie:
        kb.append([InlineKeyboardButton("📥 DOWNLOAD", callback_data=f"dl_{page}")])
    
    title = info['title'] if info else movie['title']
    poster = info['poster'] if info else movie.get('poster')
    
    # ✅ Show appropriate message
    if has_movie:
        status_text = '✅ Download Available'
    else:
        status_text = '❌ Movie not found — try another search'
    
    caption = (
        f"🎬 {title}\n\n"
        f"📊 Result {page+1} of {total}\n"
        f"{status_text}\n"
        f"⏹ Stop | ▶️ Continue\n"
    )
    
    if has_movie:
        caption += "\n👑 @Sir_logicking"
    else:
        caption += "\n\n💡 Tip: Try searching with a different name or year\n👑 @Sir_logicking"
    
    try: await msg.delete()
    except: pass
    
    try:
        if poster and has_movie:
            await msg.chat.send_photo(photo=poster, caption=caption, reply_markup=InlineKeyboardMarkup(kb))
        else:
            await msg.chat.send_message(caption, reply_markup=InlineKeyboardMarkup(kb))
    except:
        await msg.chat.send_message(caption, reply_markup=InlineKeyboardMarkup(kb))

async def handle_callback(update, context):
    q = update.callback_query; await q.answer()
    uid = update.effective_user.id; cid = q.message.chat_id
    s = sessions.get(uid)
    
    if q.data == 'how_to_use':
        await q.message.delete()
        await context.bot.send_message(cid,
            f"📖 HOW TO USE:\n\n1️⃣ Type any movie name\n2️⃣ Browse results with ⬅️➡️\n3️⃣ Click 📥 DOWNLOAD\n4️⃣ Watch progress in real-time\n5️⃣ Get your movie file!\n\n💡 PRO TIPS:\n▸ INCLUDE YEAR FOR BETTER RESULTS\n▸ You can search while downloading\n▸ Use ⏹ Stop to cancel\n\n👑 @Sir_logicking",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Start", callback_data='back_start')]]))
        return
    
    if q.data == 'search_tips':
        await q.message.delete()
        await context.bot.send_message(cid,
            f"🔍 SEARCH TIPS:\n\n✅ DO:\n▸ Include year: 'avatar 2009'\n▸ Use full name: 'jurassic world rebirth'\n▸ Try hyphens: 'spider-man-2002'\n\n❌ DON'T:\n▸ Don't use special characters\n▸ Don't type random letters\n\n💡 Bot auto-corrects typos!\n\n👑 @Sir_logicking",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Start", callback_data='back_start')]]))
        return
    
    if q.data == 'back_start':
        await q.message.delete()
        user_name = update.effective_user.first_name
        keyboard = [
            [InlineKeyboardButton("📖 How to Use", callback_data='how_to_use')],
            [InlineKeyboardButton("🔍 Search Tips", callback_data='search_tips')],
            [InlineKeyboardButton("📢 Join Channel", url=FORCE_JOIN_URL)],
            [InlineKeyboardButton("👑 Developer", url='https://t.me/Sir_logicking')],
        ]
        try:
            await context.bot.send_photo(cid, photo=BOT_PHOTO_URL,
                caption=f"🎬 MOVIE ZONE DOWNLOADER\n\n👋 Welcome, {user_name}!\n\n💡 Type a movie name to start!\n\n👑 @Sir_logicking", reply_markup=InlineKeyboardMarkup(keyboard))
        except:
            await context.bot.send_message(cid,
                f"🎬 MOVIE ZONE DOWNLOADER\n\n👋 Welcome, {user_name}!\n\n💡 Type a movie name to start!\n\n👑 @Sir_logicking", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if q.data == 'check_join':
        if await check_subscription(uid, context):
            await q.message.delete()
            await context.bot.send_message(cid, '✅ Verified!\n\nSend me a movie name!\n👑 @Sir_logicking')
        else:
            await q.answer('❌ You have not joined yet!', show_alert=True)
        return
    
    if not s: return
    if q.data == 'noop': return
    
    if q.data == 'first': s['page'] = 0; await show_movie(q.message, uid)
    elif q.data == 'last': s['page'] = len(s['movies'])-1; await show_movie(q.message, uid)
    elif q.data == 'prev':
        s['page'] -= 1
        if s['page'] < 0: s['page'] = len(s['movies'])-1
        await show_movie(q.message, uid)
    elif q.data == 'next':
        s['page'] += 1
        if s['page'] >= len(s['movies']): s['page'] = 0
        await show_movie(q.message, uid)
    elif q.data == 'stop_search':
        await q.message.delete()
        await context.bot.send_message(cid, '⏹ Search stopped!\n\nSend a new movie name.\n👑 @Sir_logicking')
        sessions.pop(uid, None)
    elif q.data == 'continue_search':
        await show_movie(q.message, uid)
    
    elif q.data.startswith('dl_'):
        page = int(q.data.replace('dl_', ''))
        movie = s['movies'][page]
        info = movie.get('info', {})
        dw = info.get('downloadwella_url')
        
        if not dw: await q.answer('❌ No link!'); return
        
        dk = f"{uid}_{page}"
        if dk in active_downloads: await q.answer('⏳ Already downloading!'); return
        
        await q.message.delete()
        pm = await context.bot.send_message(cid, '🔄 Starting download...')
        active_downloads[dk] = pm.message_id
        
        async def process():
            try:
                loop = asyncio.get_event_loop(); e_i = 0
                
                async def update_progress():
                    nonlocal e_i
                    while dk in active_downloads:
                        try:
                            bar = PROGRESS_BARS[e_i % len(PROGRESS_BARS)]
                            await pm.edit_text(f'{DOWNLOAD_EMOJIS[e_i % len(DOWNLOAD_EMOJIS)]} Processing...\n{bar}\n👑 @Sir_logicking')
                            e_i += 1; await asyncio.sleep(1)
                        except: break
                
                anim = asyncio.create_task(update_progress())
                direct = await loop.run_in_executor(download_pool, downloader.selenium_get_link, dw)
                if not direct: direct = await loop.run_in_executor(download_pool, downloader.requests_get_link, dw)
                if not direct: anim.cancel(); await pm.edit_text('❌ Failed!\n👑 @Sir_logicking'); return
                
                def dl_progress(pct, down, total):
                    try:
                        bar = PROGRESS_BARS[min(pct//10, 10)]
                        asyncio.run_coroutine_threadsafe(pm.edit_text(
                            f'📥 server is fetching...\n{bar} {pct}%\n📊 {down/1048576:.1f}/{total/1048576:.1f} MB\n👑 @Sir_logicking'), loop)
                    except: pass
                
                fp = await loop.run_in_executor(download_pool, downloader.download_file, direct, dl_progress)
                anim.cancel()
                
                if not fp: await pm.edit_text('❌ Download failed!\n👑 @Sir_logicking'); return
                
                fs = os.path.getsize(fp)
                if fs > 2000000000: cleanup_after_send(fp); await pm.edit_text('❌ >2GB!'); return
                
                await pm.edit_text(
                    f'✅ Ready!\n\n'
                    f'🎬 {info.get("title","")}\n'
                    f'📊 {fs/1048576:.1f} MB\n\n'
                    f'📥 YOUR DOWNLOAD LINK IS READY:\n'
                    f'{direct}\n\n'
                    f'☝️ Tap the link above and your movie will start downloading immediately\n'
                    f'📱 The movie saves directly to your device\n\n'
                    f'⚠️ IMPORTANT:\n'
                    f'• This link expires in ~8 hours\n'
                    f'• If link stops working, search the movie again\n\n'
                    f'⚠️ DISCLAIMER:\n'
                    f'We do NOT own, host, or store any movies.\n'
                    f'All content is fetched from publicly available\n'
                    f'third-party sources over which we have no control.\n'
                    f'If you believe any content infringes your copyright,\n'
                    f'👑 @Sir_logicking',
                    disable_web_page_preview=True
                )
            
                cleanup_after_send(fp)
            except Exception as e:
                try: await pm.edit_text(f'❌ {str(e)[:100]}')
                except: pass
            finally:
                active_downloads.pop(dk, None)
        
        asyncio.create_task(process())
        await q.answer('📥 Download started!')

def main():
    cleanup_old_files()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    print('🤖 Logic King Pro Downloader Running!')
    print('📸 Photo Header | 🔍 Auto-Correct | ⏹ Stop/Continue | 🔒 Force Join')
    print('👑 Sir_logicking')
    threading.Thread(target=start_health_server, daemon=True).start()
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
