import asyncio
import aiohttp
import itertools
import string
import os
import json
import random
from pathlib import Path
from time import time
import sys

try:
    from nltk.corpus import words
    NLTK_AVAILABLE = True
except:
    NLTK_AVAILABLE = False

VERSION = "2.2.0"

class Cfg:
    def __init__(self):
        os.makedirs("data", exist_ok=True)
        self.path = Path("data/config.json")
        if not self.path.exists():
            self.path.write_text("{}")
        
    def get(self, key, default=None):
        try:
            data = json.loads(self.path.read_text())
            return data.get(key, default)
        except:
            return default
    
    def set(self, key, value):
        try:
            data = json.loads(self.path.read_text())
        except:
            data = {}
        data[key] = value
        self.path.write_text(json.dumps(data, indent=4))

cfg = Cfg()

class Clr:
    ENDC = '\033[0m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    CYAN = '\033[36m'
    GREY = '\033[90m'

os.makedirs("logs", exist_ok=True)
os.makedirs("results", exist_ok=True)  
os.makedirs("data", exist_ok=True)

Path("data/proxies.txt").touch()
Path("data/names_to_check.txt").touch()
Path("results/hits.txt").touch()

def ld_prx():
    proxies_list = Path("data/proxies.txt").read_text().strip().splitlines()
    proxies_list = [p.strip() for p in proxies_list if p.strip()]
    if not proxies_list:
        proxies_list = [None]
    return proxies_list

class St:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.requests = 0
        self.hits = 0
        self.taken = 0
        self.errors = 0
        self.rps = 0
        self.last_requests = 0
        self.last_activity = time()
        self.active_workers = 0
        self.current_index = 0
        self.should_restart = False
        self.running = True
        self.lock = asyncio.Lock()

st = St()

def tch():
    st.last_activity = time()

def lg(msg):
    try:
        with open("logs/log.txt", "a") as f:
            f.write(f"{time()}: {msg}\n")
    except:
        pass

def sv_hit(username):
    try:
        with open("results/hits.txt", "a") as f:
            f.write(f"{username}\n")
    except:
        pass

def sv_prg(index):
    try:
        Path("data/progress.txt").write_text(str(index))
    except:
        pass

def ld_prg():
    try:
        return int(Path("data/progress.txt").read_text().strip())
    except:
        return 0

def clr_prg():
    try:
        Path("data/progress.txt").unlink()
    except:
        pass

async def dl_og(lengths: list = None):
    og_words = set()
    source_url = "https://gist.githubusercontent.com/kivox/920c271ef8dec2b33c84e1f2cc2977fc/raw/b7c95945587c76d7c7f26b930da30a9c86bf35b1/usernames.txt"
    check_all_lengths = (lengths is None or len(lengths) == 0)
    
    if check_all_lengths:
        print(f"{Clr.YELLOW}[*]{Clr.ENDC} Downloading OG usernames from usernames.txt (all lengths)...")
    else:
        print(f"{Clr.YELLOW}[*]{Clr.ENDC} Downloading OG usernames from usernames.txt (lengths: {', '.join(map(str, lengths))}L)...")
    
    async with aiohttp.ClientSession() as session:
        try:
            print(f"{Clr.CYAN}[i]{Clr.ENDC} Downloading from usernames.txt...")
            async with session.get(source_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    words_list = text.strip().splitlines()
                    
                    for word in words_list:
                        word_lower = word.lower().strip()
                        if word_lower.isalpha():
                            if check_all_lengths or len(word_lower) in lengths:
                                og_words.add(word_lower)
                    
                    print(f"{Clr.GREEN}[+]{Clr.ENDC} Loaded {len(og_words)} usernames from usernames.txt")
                else:
                    print(f"{Clr.RED}[!]{Clr.ENDC} Failed to load usernames.txt (Status: {resp.status})")
        except Exception as e:
            print(f"{Clr.RED}[!]{Clr.ENDC} Failed to load from usernames.txt: {str(e)[:50]}")
    
    if not og_words:
        print(f"{Clr.RED}[!]{Clr.ENDC} Failed to download words from usernames.txt!")
        print(f"{Clr.RED}[!]{Clr.ENDC} Please check your internet connection and try again.")
        return []
    
    return sorted(list(og_words))

async def gen_og(lengths: list = None):
    return await dl_og(lengths)

async def gen_cmb(lengths: list, letters_only: bool = False, og_mode: bool = False):
    if og_mode:
        if lengths is None:
            print(f"{Clr.YELLOW}[*]{Clr.ENDC} Generating OG words (all lengths)...")
        else:
            print(f"{Clr.YELLOW}[*]{Clr.ENDC} Generating OG words ({' and '.join([f'{l}L' for l in lengths])})...")
        combos = await gen_og(lengths)
        print(f"{Clr.GREEN}[+]{Clr.ENDC} Generated {len(combos)} OG words")
        
        combos_file = Path("data/names_to_check.txt")
        combos_file.write_text("\n".join(combos))
        
        random.shuffle(combos)
        print(f"{Clr.GREEN}[+]{Clr.ENDC} Shuffled {len(combos)} OG usernames (random order)")
        
        if lengths is None:
            length_counts = {}
            for combo in combos:
                length_counts[len(combo)] = length_counts.get(len(combo), 0) + 1
            for length in sorted(length_counts.keys()):
                print(f"{Clr.CYAN}[i]{Clr.ENDC} {length_counts[length]} {length}L OG words")
        else:
            for length in lengths:
                count = len([c for c in combos if len(c) == length])
                print(f"{Clr.CYAN}[i]{Clr.ENDC} {count} {length}L OG words")
        
        return combos
    
    if letters_only:
        CHARS = string.ascii_lowercase + "_."
        char_type = "letters only (a-z, _, .)"
    else:
        CHARS = string.ascii_lowercase + string.digits + "_."
        char_type = "letters + numbers (a-z, 0-9, _, .)"
    
    combos_file = Path("data/names_to_check.txt")
    combos = combos_file.read_text().strip().splitlines()
    combos = [c.strip() for c in combos if c.strip()]
    
    if combos:
        combos = [c for c in combos if len(c) in lengths]
        if letters_only:
            combos = [c for c in combos if not any(char.isdigit() for char in c)]
    
    if not combos:
        length_names = " and ".join([f"{l}L" for l in lengths])
        print(f"{Clr.YELLOW}[*]{Clr.ENDC} Generating {length_names} combinations ({char_type})...")
        
        all_combos = []
        for length in lengths:
            for combo in itertools.product(CHARS, repeat=length):
                all_combos.append("".join(combo))
        
        combos_file.write_text("\n".join(all_combos))
        combos = all_combos
        print(f"{Clr.GREEN}[+]{Clr.ENDC} Generated {len(combos)} combinations")
    
    random.shuffle(combos)
    print(f"{Clr.GREEN}[+]{Clr.ENDC} Shuffled {len(combos)} usernames (random order)")
    
    for length in lengths:
        count = len([c for c in combos if len(c) == length])
        print(f"{Clr.CYAN}[i]{Clr.ENDC} {count} {length}L usernames")
    
    return combos

class Chk:
    def __init__(self):
        self.endpoint = "https://discord.com/api/v9/unique-username/username-attempt-unauthed"
        self.headers = {"Content-Type": "application/json"}
        self.timeout = aiohttp.ClientTimeout(total=5, connect=3)
        self.session = None
        self.proxy_cycle = None
        self.proxy_lock = asyncio.Lock()
    
    async def create_session(self):
        if self.session:
            try:
                await asyncio.wait_for(self.session.close(), timeout=2)
            except:
                pass
        
        connector = aiohttp.TCPConnector(limit=100, ttl_dns_cache=300, force_close=True)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=self.timeout,
            headers=self.headers
        )
        
        proxies = ld_prx()
        self.proxy_cycle = itertools.cycle(proxies)
        print(f"{Clr.GREEN}[+]{Clr.ENDC} Session created with {len(proxies)} proxies")
    
    async def get_proxy(self):
        async with self.proxy_lock:
            return next(self.proxy_cycle)
    
    async def close(self):
        if self.session:
            try:
                await asyncio.wait_for(self.session.close(), timeout=2)
            except:
                pass
    
    async def check(self, username: str) -> tuple:
        max_retries = 3
        
        for attempt in range(max_retries):
            if not st.running:
                return (None, {})
            
            proxy = await self.get_proxy()
            proxy_url = f"http://{proxy}" if proxy else None
            
            try:
                async def do_request():
                    async with self.session.post(
                        self.endpoint,
                        json={"username": username},
                        proxy=proxy_url
                    ) as resp:
                        st.requests += 1
                        tch()
                        
                        if resp.status in (200, 201, 204):
                            data = await resp.json()
                            tch()
                            taken = data.get("taken")
                            
                            if taken is True:
                                st.taken += 1
                                return (False, data)
                            elif taken is False:
                                st.hits += 1
                                return (True, data)
                            else:
                                return (None, {})
                        
                        elif resp.status == 429:
                            tch()
                            await asyncio.sleep(0.5)
                            return (None, {})
                        else:
                            tch()
                            return (None, {})
                
                result = await asyncio.wait_for(do_request(), timeout=6)
                if result[0] is not None:
                    return result
                continue
                            
            except asyncio.TimeoutError:
                tch()
                continue
            except Exception as e:
                tch()
                continue
        
        st.errors += 1
        return (None, {})

chk = Chk()

async def wrk(combos: list, worker_id: int):
    st.active_workers += 1
    consecutive_fails = 0
    
    try:
        while st.running:
            async with st.lock:
                if st.current_index >= len(combos):
                    break
                idx = st.current_index
                st.current_index += 1
            
            tch()
            
            username = combos[idx]
            
            if idx % 50 == 0:
                sv_prg(idx)
            
            try:
                result = await asyncio.wait_for(
                    chk.check(username),
                    timeout=8
                )
                
                if not st.running:
                    break
                
                available, resp = result
                
                if available is True:
                    tch()
                    print(f"[{Clr.GREEN}+{Clr.ENDC}] Available: {Clr.CYAN}{username}{Clr.ENDC} | RPS: {st.rps} | {idx}/{len(combos)}")
                    sv_hit(username)
                    consecutive_fails = 0
                elif available is False:
                    tch()
                    print(f"[{Clr.RED}-{Clr.ENDC}]   Taken  : {Clr.CYAN}{username}{Clr.ENDC} | RPS: {st.rps}")
                    consecutive_fails = 0
                else:
                    consecutive_fails += 1
                    if consecutive_fails > 10:
                        await asyncio.sleep(1)
                        consecutive_fails = 0
                
            except asyncio.TimeoutError:
                tch()
                lg(f"Worker {worker_id} timeout on {username}")
                consecutive_fails += 1
            except Exception as e:
                tch()
                lg(f"Worker {worker_id} error: {str(e)[:50]}")
                consecutive_fails += 1
            
            await asyncio.sleep(0.01)
    
    except Exception as e:
        lg(f"Worker {worker_id} fatal: {str(e)}")
    finally:
        st.active_workers -= 1

async def rps_calc():
    while st.running:
        try:
            st.last_requests = st.requests
            await asyncio.sleep(1)
            st.rps = st.requests - st.last_requests
        except:
            await asyncio.sleep(1)

async def wd(combos: list):
    while st.running:
        await asyncio.sleep(0.5)
        
        if st.current_index >= len(combos):
            continue
        
        idle = time() - st.last_activity
        
        if 3 <= idle < 5:
            print(f"{Clr.YELLOW}[W]{Clr.ENDC} {int(idle)}s idle - will restart at 5s", end="\r")
        
        if idle >= 5:
            print(f"\n\n{Clr.YELLOW}[!]{Clr.ENDC} STALL DETECTED - {int(idle)}s idle")
            print(f"{Clr.YELLOW}[!]{Clr.ENDC} Restarting from {st.current_index}/{len(combos)}...\n")
            lg(f"RESTART: index {st.current_index}, idle {idle}s, workers {st.active_workers}")
            
            st.should_restart = True
            st.running = False
            break

async def hb():
    while st.running:
        await asyncio.sleep(2)
        if st.rps > 0 or st.requests > 0:
            pass

async def tt_upd(total: int):
    if os.name != "nt":
        return
    
    while st.running:
        try:
            title = f"CloudChecker - Hits {st.hits} - {st.current_index}/{total} - RPS {st.rps}"
            os.system(f"title {title}")
            await asyncio.sleep(2)
        except:
            await asyncio.sleep(2)

async def run_chk(combos: list, num_workers: int, start_index: int):
    st.reset()
    st.current_index = start_index
    
    print(f"\n{Clr.GREEN}[+]{Clr.ENDC} Starting from index {start_index}")
    print(f"{Clr.GREEN}[+]{Clr.ENDC} Running with {num_workers} workers\n")
    
    await chk.create_session()
    
    tasks = [
        asyncio.create_task(rps_calc()),
        asyncio.create_task(wd(combos)),
        asyncio.create_task(tt_upd(len(combos))),
    ]
    
    worker_tasks = [
        asyncio.create_task(wrk(combos, i))
        for i in range(num_workers)
    ]
    
    try:
        await asyncio.gather(*worker_tasks, return_exceptions=True)
    except:
        pass
    
    for task in tasks + worker_tasks:
        task.cancel()
        try:
            await asyncio.wait_for(task, timeout=1)
        except:
            pass
    
    await chk.close()
    
    return st.should_restart, st.current_index

async def mn():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    if cfg.get("timeout") is None:
        cfg.set("timeout", 5)
    
    print(f"\n{Clr.CYAN}[?]{Clr.ENDC} Check mode:")
    print(f"  1) Regular combinations (3-4L)")
    print(f"  2) OG words (all lengths from usernames.txt like amon, audrey, klein)")
    mode_choice = input(f"Choice [1/2] {Clr.YELLOW}>>>{Clr.ENDC} ").strip()
    
    og_mode = (mode_choice == "2")
    
    if og_mode:
        print(f"\n{Clr.CYAN}[?]{Clr.ENDC} Which OG word lengths to check?")
        print(f"  1) All lengths (no limit)")
        print(f"  2) 4 letters only")
        print(f"  3) 5 letters only")
        print(f"  4) Both 4 and 5 letters")
        print(f"  5) Custom lengths (comma separated, e.g., 3,4,5)")
        choice = input(f"Choice [1/2/3/4/5] {Clr.YELLOW}>>>{Clr.ENDC} ").strip()
        
        if choice == "1":
            lengths = None
        elif choice == "2":
            lengths = [4]
        elif choice == "3":
            lengths = [5]
        elif choice == "4":
            lengths = [4, 5]
        elif choice == "5":
            custom_input = input(f"Enter lengths (comma separated, e.g., 3,4,5) {Clr.YELLOW}>>>{Clr.ENDC} ").strip()
            try:
                lengths = [int(x.strip()) for x in custom_input.split(",") if x.strip().isdigit()]
                if not lengths:
                    print(f"{Clr.RED}[!]{Clr.ENDC} Invalid input, using all lengths")
                    lengths = None
            except:
                print(f"{Clr.RED}[!]{Clr.ENDC} Invalid input, using all lengths")
                lengths = None
        else:
            lengths = None
        
        combos = await gen_cmb(lengths, letters_only=False, og_mode=True)
    else:
        print(f"\n{Clr.CYAN}[?]{Clr.ENDC} Which username lengths to check?")
        print(f"  1) 3 digits only")
        print(f"  2) 4 digits only")
        print(f"  3) Both 3 and 4 digits")
        choice = input(f"Choice [1/2/3] {Clr.YELLOW}>>>{Clr.ENDC} ").strip()
        
        if choice == "1":
            lengths = [3]
        elif choice == "2":
            lengths = [4]
        else:
            lengths = [3, 4]
        
        print(f"\n{Clr.CYAN}[?]{Clr.ENDC} Character set:")
        print(f"  1) Letters only (a-z, _, .)")
        print(f"  2) Letters + Numbers (a-z, 0-9, _, .)")
        char_choice = input(f"Choice [1/2] {Clr.YELLOW}>>>{Clr.ENDC} ").strip()
        
        letters_only = (char_choice == "1")
        
        combos = await gen_cmb(lengths, letters_only, og_mode=False)
    if not combos:
        print(f"{Clr.RED}[!] No usernames{Clr.ENDC}")
        return
    
    saved_progress = ld_prg()
    if saved_progress > 0:
        resume = input(f"\nResume from {saved_progress}? [y/n] {Clr.YELLOW}>>>{Clr.ENDC} ").lower()
        if resume not in ["y", "yes", "1"]:
            saved_progress = 0
            clr_prg()
    
    if saved_progress == 0:
        clear_hits = input(f"Clear old hits? [y/n] {Clr.YELLOW}>>>{Clr.ENDC} ").lower()
        if clear_hits in ["y", "yes", "1"]:
            Path("results/hits.txt").write_text("")
    
    num_workers = input(f"\nHow many workers? {Clr.YELLOW}>>>{Clr.ENDC} ")
    try:
        num_workers = int(num_workers)
    except:
        num_workers = 10
    num_workers = max(1, min(num_workers, 50))
    
    print(f"\n{Clr.YELLOW}[*]{Clr.ENDC} Starting in 3 seconds...")
    await asyncio.sleep(3)
    
    current_index = saved_progress
    restart_count = 0
    start_time = time()
    
    while current_index < len(combos):
        os.system('cls' if os.name == 'nt' else 'clear')
        
        if restart_count > 0:
            print(f"{Clr.YELLOW}[!] Auto-restart #{restart_count}{Clr.ENDC}")
        
        should_restart, new_index = await run_chk(combos, num_workers, current_index)
        
        if should_restart:
            restart_count += 1
            current_index = new_index
            sv_prg(current_index)
            print(f"\n{Clr.CYAN}[i]{Clr.ENDC} Restarting in 3 seconds...\n")
            await asyncio.sleep(3)
        else:
            break
    
    elapsed = int(time() - start_time)
    print(f"\n\n{Clr.GREEN}{'='*50}{Clr.ENDC}")
    print(f"{Clr.GREEN}[+]{Clr.ENDC} DONE!")
    print(f"{Clr.GREEN}[+]{Clr.ENDC} Requests: {st.requests}")
    print(f"{Clr.GREEN}[+]{Clr.ENDC} Available: {Clr.GREEN}{st.hits}{Clr.ENDC}")
    print(f"{Clr.GREEN}[+]{Clr.ENDC} Taken: {st.taken}")
    print(f"{Clr.GREEN}[+]{Clr.ENDC} Restarts: {restart_count}")
    print(f"{Clr.GREEN}[+]{Clr.ENDC} Time: {elapsed}s")
    print(f"{Clr.GREEN}{'='*50}{Clr.ENDC}\n")
    
    clr_prg()

if __name__ == "__main__":
    try:
        asyncio.run(mn())
    except KeyboardInterrupt:
        print(f"\n{Clr.YELLOW}[!]{Clr.ENDC} Interrupted - progress saved")
        sys.exit(0)
