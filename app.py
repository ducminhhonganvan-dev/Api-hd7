import os, sys, time, json, socket, random, threading, asyncio, io
import requests, aiohttp
from datetime import datetime, timedelta, timezone
import pytz
import telebot
from flask import Flask, request, jsonify
from status.status_lib import *
from status.status_GP import *
from status.STATUS_API import *
from status.STATUS_API import FreeFireAPI

class FreeFireTCP:
 def __init__(self, bot_config, manager):
  self.bot_config, self.manager = bot_config, manager
  self.running_event = threading.Event()
  self.running_event.set()
  self.status, self.started = True, False
  self.base_url = "https://clientbp.ggblueshark.com"
  self.reconnect_lock = threading.Lock()
  self.last_spam_time = {}
  self.roomcode = self.packetAuth = self.playerstatus = self.AuthenCode = self.sock39699 = self.sock39801 = None
  self.ChatIP = self.OnlineIP = self.OnlinePort = self.ChatPort = self.roomid = self.GuildIds = self.DesId = self.botid = None
  self.key = self.iv = self.token = b''
  self.login_session = self._data = self.nickname = self.region = None

 def _IIl(self, logindata, jsdata):
  self.cleanup()
  time.sleep(0.5)
  self._gen, self._bot = TAO_PACKET(logindata, jsdata), self.bot_session(self)
  self.running_event.set()
  time.sleep(1)
  threading.Thread(target=self.connect39801, daemon=True).start()
  threading.Thread(target=self.connect39699, daemon=True).start()

 def update_config(self, new_config): self.bot_config = new_config
 
 def cleanup(self):
  self.running_event.clear()
  for sock in [self.sock39699, self.sock39801]:
   try:
    if sock: sock.shutdown(2); sock.close()
   except: pass
  self.sock39699 = self.sock39801 = None

 def restart_bot(self):
  self.cleanup()
  time.sleep(2)
  self.running_event.set()
  self.started = False
  self.start()

 def AntiDisconnect(self, sock):
  while True: sock.send(bytes([0, 2, 0, 1])); time.sleep(25)

 def connect39801(self):
  with self.reconnect_lock:
   if not self.running_event.is_set(): return
   client = None
   try:
    client = socket.create_connection((self.ChatIP, int(self.ChatPort)))
    client.sendall(self.packetAuth)
    if self.GuildIds and self.bot_config.get("active-clan", True): client.send(self._bot.join_channel(self.GuildIds, self.AuthenCode, 1))
    client.send(self._bot.join_channel(None, None, 5))
    self.sock39801 = client
    while self.running_event.is_set():
     data = client.recv(3300)
     if not data: break
     if data.hex()[:4] == "1200" and len(data) > 50: threading.Thread(target=self.C1200, args=(data, client,)).start()
   except: pass
   finally:
    if client:
     try: client.close()
     except: pass
    self.sock39801 = None
    if self.running_event.is_set(): time.sleep(5); threading.Thread(target=self.connect39801, daemon=True).start()

 def connect39699(self):
  if not self.running_event.is_set(): return
  client = None
  try:
   client = socket.create_connection((self.OnlineIP, int(self.OnlinePort)))
   client.sendall(self.packetAuth)
   self.sock39699 = client
   while self.running_event.is_set():
    data = client.recv(3300)
    if not data: break
    if data.hex()[:4] == "0f00":
     decdata = json.loads(protobuf_dec(data.hex()[10:]))
     self.playerstatus, rid = decdata, decdata.get("5").get("1").get("15", None)
     self.roomid = rid if rid else None
  except: pass
  finally:
   if client:
    try: client.close()
    except: pass
   self.sock39699 = None
   if self.running_event.is_set(): time.sleep(3); threading.Thread(target=self.connect39699, daemon=True).start()

 def C1200(self, data, client):
  try:
   data = data1200(data)
   if not data.valid: return False
   uid, cid, type, message, name = data.uid, data.cid, data.type, data.message, data.name
   if int(self.botid) in [cid, uid]: return False
   idlist = self.get_user_status(1)
   if uid not in idlist and type in [2, None]: self._bot.reply(cid, type, "...")
   else: return False
  except: pass

 def leave(self, uid, delay):
  try:
   time.sleep(int(delay))
   self.sock39801.send(self._bot.leave_channel(uid, None))
   self.sock39699.send(self._bot.leave_squad(uid))
  except: pass

 def get_user_status(self, type, uid=None):
  if type == 1: return [u["uid"] for u in self.bot_config.get("access_bot", [])] + [self.botid] + [self.GuildIds]
  if type in [2, 3] and uid is not None:
   for u in self.bot_config.get("access_bot", []):
    if u["uid"] == int(uid):
     try:
      exp_time = datetime.datetime.strptime(u["expire"], "%Y-%m-%d %H:%M:%S")
      now = datetime.datetime.now()
      if exp_time < now: self.manager.deleteId(self.bot_config["bot_id"], uid); return False
      if type == 2: return True, False
      delta = exp_time - now
      parts = [f"{delta.days} Days" if delta.days else "", f"{delta.seconds // 3600} hour" if delta.seconds // 3600 else "", f"{(delta.seconds % 3600) // 60} minute" if (delta.seconds % 3600) // 60 else ""]
      return ", ".join(filter(None, parts))
     except: return False if type == 2 else "null"
   return "∞"
  return "∞"

 class bot_session:
  def __init__(self, parent): self.par = parent
  def __getattr__(self, name): return getattr(self.par._gen, name)
  def reply(self, Id, Tp, Ms):
   try:
    if self.par.running_event.is_set() and self.par.sock39801: self.par.sock39801.sendall(self.par._gen.send_message(Ms, Tp, Id))
   except: pass

 def rstart(self):
  access_token = self.bot_config['auth_bot_login']['access_token']
  while self.running_event.is_set():
   try:
    data = FreeFireAPI().get(access_token, is_emulator=False)
    if "account not found" in data: self.running_event.clear(); break
    if data.get("GuildData"): self.AuthenCode, self.GuildIds = data.get("GuildData").get("secret_code"), data.get("GuildData").get("id")
    self.packetAuth, self.botid, self.nickname, self.region, self.token = bytes(data["UserAuthPacket"]), int(data["UserAccountUID"]), str(data["UserNickName"]), str(data["LockRegion"]), data["UserAuthToken"]
    self.ChatIP, self.OnlineIP, self.OnlinePort, self.ChatPort = data["GameServerAddress"]["chatip"], data["GameServerAddress"]["onlineip"], data["GameServerAddress"]["onlineport"], data["GameServerAddress"]["chatport"]
    self.key, self.iv, self.base_url = bytes(data["key"]), bytes(data["iv"]), data["BaseUrl"]
    ChooseEmote(self.token, self.base_url); self._IIl(data["logindata"], data)
    if not self.running_event.is_set(): break
    time.sleep(14555)
   except:
    if self.running_event.is_set(): time.sleep(1111)

 def start(self):
  if self.started: return
  self.started = True
  self.running_event.set()
  threading.Thread(target=self.rstart, daemon=True).start()

class BOTMNG:
 def __init__(self):
  self.bots, self.config_lock, self.filename = {}, threading.RLock(), "bot.json"
  self.load_config()
  threading.Thread(target=self.auto_cleanup_expired_users, daemon=True).start()

 def load_config(self):
  try:
   self.config = json.loads(File.check(self.filename)[1])
   if "bots" not in self.config: self.config["bots"] = []
   for bot_data in self.config["bots"]:
    bot_id = bot_data["bot_id"]
    bot_instance = FreeFireTCP(bot_data, self)
    if "botid" in bot_data: bot_instance.botid = bot_data["botid"]
    if "nickname" in bot_data: bot_instance.nickname = bot_data["nickname"]
    self.bots[bot_id] = bot_instance
  except: self.config = {"bots": []}; self.save_config()

 def save_config(self):
  try:
   with self.config_lock:
    for bot_id, bot_instance in self.bots.items():
     for bot_config in self.config["bots"]:
      if bot_config["bot_id"] == bot_id:
       if hasattr(bot_instance, 'botid') and bot_instance.botid: bot_config["botid"] = bot_instance.botid
       if hasattr(bot_instance, 'nickname') and bot_instance.nickname: bot_config["nickname"] = bot_instance.nickname
    File.edit(self.filename, self.config)
  except: pass

 def get_next_bot_id(self):
  with self.config_lock: return max([bot["bot_id"] for bot in self.config["bots"]] + [0]) + 1

 def check_token_exists(self, access_token):
  with self.config_lock:
   for bot in self.config["bots"]:
    if bot["auth_bot_login"]["access_token"] == access_token: return True, bot["bot_id"]
   return False, None

 def toggle_guild_activation(self, bot_id, action):
  with self.config_lock:
   try:
    bot_id = int(bot_id)
    for bot in self.config["bots"]:
     if bot["bot_id"] == bot_id:
      if bot_id not in self.bots: return "error"
      bot_instance = self.bots[bot_id]
      if not bot_instance.GuildIds: return "Bot is not in guild"
      active = action == "on"
      bot["active-clan"] = bot_instance.bot_config["active-clan"] = active
      self.save_config(); threading.Thread(target=bot_instance.restart_bot).start()
      return "active" if active else "Inactive"
   except: pass
   return "error"

 def add_bot(self, access_token, bot_cmd_data=None):
  with self.config_lock:
   exists, existing_bot_id = self.check_token_exists(access_token)
   if exists: return {"status": False, "message": "access token already exists"}
   bot_id = self.get_next_bot_id()
   new_bot = {"bot_id": bot_id, "auth_bot_login": {"access_token": access_token}, "access_bot": [], "active-clan": True}
   self.config["bots"].append(new_bot); self.save_config(); self.bots[bot_id] = FreeFireTCP(new_bot, self)
   return {"status": True, "bot_id": bot_id}

 def delete_bot(self, bot_id):
  with self.config_lock:
   if bot_id in self.bots:
    try: self.bots[bot_id].cleanup()
    except: pass
    del self.bots[bot_id]
    self.config["bots"] = [b for b in self.config["bots"] if b["bot_id"] != bot_id]
    self.save_config(); return True
   return False

 def remove_bot(self, bot_id):
  with self.config_lock:
   if bot_id in self.bots:
    bot_instance = self.bots[bot_id]
    bot_instance.cleanup(); del self.bots[bot_id]
    if not getattr(bot_instance, 'is_temporary', False): self.config["bots"] = [b for b in self.config["bots"] if b["bot_id"] != bot_id]; self.save_config()
    return True
   return False

 def deleteId(self, bot_id, uid):
  with self.config_lock:
   try: uid = int(uid)
   except: return False
   for bot in self.config["bots"]:
    if bot["bot_id"] == bot_id:
     access = bot.get("access_bot", [])
     new_access = [u for u in access if u["uid"] != uid]
     if len(new_access) != len(access):
      bot["access_bot"] = new_access
      if bot_id in self.bots: self.bots[bot_id].bot_config = bot; self.save_config(); return True
     return False
  return False

 def auto_cleanup_expired_users(self):
  while True:
   try:
    now, total_cleaned = datetime.datetime.now(), 0
    with self.config_lock:
     for bot_config in self.config["bots"]:
      bot_id = bot_config["bot_id"]
      expired_users = []
      for user in bot_config.get("access_bot", []):
       try:
        if datetime.datetime.strptime(user["expire"], "%Y-%m-%d %H:%M:%S") < now: expired_users.append(user["uid"])
       except: expired_users.append(user.get("uid"))
      if expired_users:
       bot_config["access_bot"] = [u for u in bot_config["access_bot"] if u["uid"] not in expired_users]
       if bot_id in self.bots: self.bots[bot_id].bot_config = bot_config
       total_cleaned += len(expired_users)
     if total_cleaned > 0: self.save_config()
   except: pass
   time.sleep(3600)

TCPbot = BOTMNG()
app = Flask(__name__)
is_running_sf = False

def get_bot():
 try: return list(TCPbot.bots.values())[0]
 except: return None

@app.route('/join', methods=['GET'])
def api_sf_join():
 global is_running_sf
 if is_running_sf: return jsonify({"status": "busy"}), 400
 tcode = request.args.get('tc')
 if not tcode: return jsonify({"status": "error", "msg": "missing teamcode"}), 400
 b = get_bot()
 if not b or not b.sock39699: return jsonify({"status": "offline"}), 400
 try:
  uids = list(dict.fromkeys([int(b.botid)] + [int(request.args.get(f'uid{i}')) for i in range(1, 7) if request.args.get(f'uid{i}') and request.args.get(f'uid{i}').strip().isdigit()]))
  is_running_sf = True
  b.sock39699.send(b._bot.join_squad(int(tcode)))
  
  def run_sf_logic():
   global is_running_sf
   # TẤT CẢ CÁC MÃ ID BẠN CUNG CẤP
   evo_guns = [
       909045001, 909035007, 909049010, 909041005, 909038010, 
       909039011, 909040010, 909000081, 909000085, 909000063, 
       909000075, 909033001, 909000090, 909000068, 909000098, 
       909051003, 909037011, 909038012, 909035012, 909042008, 
       909033002, 909042007
   ]
   try:
    # Chọn ngẫu nhiên 1 hành động từ danh sách trên
    random_action = random.choice(evo_guns)
    
    if b.sock39699 and b.running_event.is_set(): 
        b.sock39699.send(b._bot.play_emote(random_action, uids))
        time.sleep(7.5) # Thời gian chờ múa
        
    if b.sock39699: b.sock39699.send(b._bot.leave_squad(0x00))
   finally: is_running_sf = False
  
  threading.Thread(target=run_sf_logic, daemon=True).start()
  return jsonify({"status": "success", "bot": b.botid, "targets": uids})
 except Exception as e: is_running_sf = False; return jsonify({"status": "error", "msg": str(e)}), 500

def Start_Single_Bot():
 tk = "4792785495:nhathoaz_J7O3B_BY_STAR_GMR_YA6Z8"
 if not TCPbot.check_token_exists(tk)[0]: TCPbot.add_bot(tk)
 time.sleep(2)
 b = get_bot()
 if b and not b.started: b.start()

if __name__ == "__main__":
 threading.Thread(target=Start_Single_Bot, daemon=True).start()
 app.run(host="0.0.0.0", port=5000)
 