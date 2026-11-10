# ThanhDora | DoraTeam | https://github.com/ThanhDora | @DoraTeamMods
"""
Apache License 2.0
"""

# database imports
import motor.motor_asyncio, datetime, pytz
from pymongo.errors import DuplicateKeyError

# bots imports
from config import Config
from helper.utils import send_log, send_pending_approval_notification

class Database:
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.user
        self.premium = self.db.premium

    def new_user(self, id):
        return dict(
            _id=int(id),
            join_date=datetime.date.today().isoformat(),
            file_id=None,
            caption=None,
            prefix=None,
            suffix=None,
            used_limit=0,
            usertype="Free",
            uploadlimit=Config.FREE_UPLOAD_LIMIT,
            daily=0,
            metadata_mode=False,
            metadata_code="--change-title @DoraTeamMods\n--change-video-title @DoraTeamMods\n--change-audio-title @DoraTeamMods\n--change-subtitle-title @DoraTeamMods\n--change-author @DoraTeamMods",
            expiry_time=None,
            has_free_trial=False,
            ban_status=dict(
                is_banned=False,
                ban_duration=0,
                banned_on=datetime.date.max.isoformat(),
                ban_reason=''
            ),
            approved=False
        )

    async def add_user(self, b, m):
        u = m.from_user
        if not await self.is_user_exist(u.id):
            user = self.new_user(u.id)
            await self.col.insert_one(user)
            await send_log(b, u)
            if getattr(Config, "APPROVAL_REQUIRED", False):
                await send_pending_approval_notification(b, u)

    async def is_user_exist(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return bool(user)

    async def ensure_user(self, user_id):
        """Create a default user document if this id has never /start'ed."""
        uid = int(user_id)
        user = await self.col.find_one({'_id': uid})
        if user:
            return user
        doc = self.new_user(uid)
        try:
            await self.col.insert_one(doc)
            return doc
        except DuplicateKeyError:
            user = await self.col.find_one({'_id': uid})
            if user:
                return user
            raise

    async def is_approved(self, user_id):
        if not getattr(Config, "APPROVAL_REQUIRED", False):
            return True
        user = await self.col.find_one({'_id': int(user_id)})
        if not user:
            return False
        return user.get("approved", True)

    async def set_approved(self, user_id, approved):
        await self.ensure_user(user_id)
        await self.col.update_one({'_id': int(user_id)}, {'$set': {'approved': bool(approved)}})

    async def get_pending_users(self):
        return self.col.find({"approved": False})

    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count

    async def get_all_users(self):
        all_users = self.col.find({})
        return all_users

    async def delete_user(self, user_id):
        uid = int(user_id)
        await self.col.delete_many({'_id': uid})
        await self.premium.delete_many({'id': uid})
    
    async def set_thumbnail(self, id, file_id):
        await self.ensure_user(id)
        await self.col.update_one({'_id': int(id)}, {'$set': {'file_id': file_id}})

    async def get_thumbnail(self, id):
        user = await self.get_user_data(id)
        return user.get('file_id', None)

    async def set_caption(self, id, caption):
        await self.ensure_user(id)
        await self.col.update_one({'_id': int(id)}, {'$set': {'caption': caption}})

    async def get_caption(self, id):
        user = await self.get_user_data(id)
        return user.get('caption', None)

    async def set_prefix(self, id, prefix):
        await self.ensure_user(id)
        await self.col.update_one({'_id': int(id)}, {'$set': {'prefix': prefix}})

    async def get_prefix(self, id):
        user = await self.get_user_data(id)
        return user.get('prefix', None)

    async def set_suffix(self, id, suffix):
        await self.ensure_user(id)
        await self.col.update_one({'_id': int(id)}, {'$set': {'suffix': suffix}})

    async def get_suffix(self, id):
        user = await self.get_user_data(id)
        return user.get('suffix', None)

    async def set_metadata_mode(self, id, bool_meta):
        await self.ensure_user(id)
        await self.col.update_one({'_id': int(id)}, {'$set': {'metadata_mode': bool_meta}})

    async def get_metadata_mode(self, id):
        user = await self.get_user_data(id)
        return user.get('metadata_mode', None)

    async def set_metadata_code(self, id, metadata_code):
        await self.ensure_user(id)
        await self.col.update_one({'_id': int(id)}, {'$set': {'metadata_code': metadata_code}})

    async def get_metadata_code(self, id):
        user = await self.get_user_data(id)
        return user.get('metadata_code', None)

    async def set_used_limit(self, id, used):
        await self.ensure_user(id)
        await self.col.update_one({'_id': int(id)}, {'$set': {'used_limit': used}})
      
    async def set_usertype(self, id, type):
        await self.ensure_user(id)
        await self.col.update_one({'_id': int(id)}, {'$set': {'usertype': type}})

    async def set_uploadlimit(self, id, limit):
        await self.ensure_user(id)
        await self.col.update_one({'_id': int(id)}, {'$set': {'uploadlimit': limit}})
  
    async def set_reset_dailylimit(self, id, date):
        await self.ensure_user(id)
        await self.col.update_one({'_id': int(id)}, {'$set': {'daily': date}})
        
    async def reset_uploadlimit_access(self, user_id):
        seconds = 1440 * 60
        reset_date = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        zero_usage = 0
        
        user_data = await self.get_user_data(user_id)
        if user_data:
            expiry_time = user_data.get("daily")
            current_time = datetime.datetime.now()
            
            needs_reset = (
                expiry_time is None or
                expiry_time == 0 or
                not isinstance(expiry_time, datetime.datetime) or
                current_time > expiry_time
            )
            
            if needs_reset:
                await self.col.update_one(
                    {'_id': user_id}, 
                    {'$set': {
                        'daily': reset_date,
                        'used_limit': zero_usage
                    }}
                )
                        
    async def get_user_data(self, id) -> dict:
        return await self.ensure_user(id)
        
    async def get_user(self, user_id):
        user_data = await self.premium.find_one({"id": user_id})
        return user_data

    async def add_premium(self, user_id, user_data, limit=None, type=None):
        await self.ensure_user(user_id)
        await self.premium.update_one(
            {"id": user_id}, 
            {"$set": user_data}, 
            upsert=True
        )
        
        if Config.UPLOAD_LIMIT_MODE and limit and type:
            await self.col.update_one(
                {'_id': user_id}, 
                {'$set': {
                    'usertype': type,
                    'uploadlimit': limit
                }}
            )

    addpremium = add_premium

    async def remove_premium(self, user_id, limit=Config.FREE_UPLOAD_LIMIT, type="Free"):
        await self.ensure_user(user_id)
        await self.premium.update_one(
            {"id": user_id}, 
            {"$set": {
                "expiry_time": None,
                "has_free_trial": False
            }}
        )
        
        if Config.UPLOAD_LIMIT_MODE and limit and type:
            await self.col.update_one(
                {'_id': user_id}, 
                {'$set': {
                    'usertype': type,
                    'uploadlimit': limit
                }}
            )
          
    async def checking_remaining_time(self, user_id):
        user_data = await self.get_user(user_id) or {}
        expiry_time = user_data.get("expiry_time")
        if not expiry_time:
            return None
        return expiry_time - datetime.datetime.now()

    async def has_premium_access(self, user_id):
        user_data = await self.get_user(user_id)
        if user_data:
            expiry_time = user_data.get("expiry_time")
            if expiry_time is None:
                # User previously used the free trial, but it has ended.
                return False
            elif isinstance(expiry_time, datetime.datetime) and datetime.datetime.now() <= expiry_time:
                return True
            else:
                await self.remove_premium(user_id)
        return False

    async def total_premium_users_count(self):
        count = await self.premium.count_documents({"expiry_time": {"$gt": datetime.datetime.now()}})
        return count

    async def get_all_premium_users(self):
        all_premium_users = self.premium.find({"expiry_time": {"$gt": datetime.datetime.now()}})
        return all_premium_users

    async def count_users_by(self, query):
        return await self.col.count_documents(query or {})

    async def list_users_page(self, query, skip=0, limit=6):
        cursor = self.col.find(query or {}).sort([("join_date", 1), ("_id", 1)]).skip(int(skip)).limit(int(limit))
        return await cursor.to_list(length=int(limit))

    async def get_free_trial_status(self, user_id):
        user_data = await self.get_user(user_id)
        if user_data:
            return user_data.get("has_free_trial", False)
        return False

    async def give_free_trial(self, user_id):
        seconds = 720 * 60
        expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        user_data = {
            "id": user_id, 
            "expiry_time": expiry_time, 
            "has_free_trial": True
        }
        
        if Config.UPLOAD_LIMIT_MODE:
            limit_type = "Trial"
            upload_limit = 536870912000
            await self.add_premium(user_id, user_data, upload_limit, limit_type)
        else:
            await self.add_premium(user_id, user_data)
                    
    async def remove_ban(self, id):
        ban_status = dict(
            is_banned=False,
            ban_duration=0,
            banned_on=datetime.date.max.isoformat(),
            ban_reason=''
        )
        await self.ensure_user(id)
        await self.col.update_one({'_id': int(id)}, {'$set': {'ban_status': ban_status}})

    async def ban_user(self, user_id, ban_duration, ban_reason):
        ban_status = dict(
            is_banned=True,
            ban_duration=ban_duration,
            banned_on=datetime.date.today().isoformat(),
            ban_reason=ban_reason)
        await self.ensure_user(user_id)
        await self.col.update_one(
            {'_id': int(user_id)},
            {'$set': {'ban_status': ban_status}},
            upsert=True
        )

    async def get_ban_status(self, id):
        default = dict(
            is_banned=False,
            ban_duration=0,
            banned_on=datetime.date.max.isoformat(),
            ban_reason='')
        user = await self.col.find_one({'_id': int(id)})
        if not user:
            return default
        return user.get('ban_status', default)

    async def get_all_banned_users(self):
        banned_users = self.col.find({'ban_status.is_banned': True})
        return banned_users
        
digital_botz = Database(Config.DB_URL, Config.DB_NAME)

# Rkn Developer 
# Don't Remove Credit 😔
# ThanhDora | DoraTeam | @DoraTeamMods
