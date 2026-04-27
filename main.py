import discord
from discord.ext import commands, tasks
import asyncio
import os
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=["!", "/"], intents=intents)

# ========== معلومات المطور ==========
DEV_NAME = "Mr Snani"
DEV_ID = 123456789012345678  # ⚠️ استبدل هذا بـ ID حسابك الحقيقي من Discord

# ========== أنظمة التتبع المتقدمة ==========
raid_tracker = defaultdict(list)
spam_tracker = defaultdict(list)
join_tracker = defaultdict(list)
delete_tracker = defaultdict(list)
attackers_tracker = defaultdict(list)
bot_detection_tracker = defaultdict(list)
suspicious_links_tracker = defaultdict(list)
report_channel_id = None

# قائمة البوتات غير الآمنة
UNSAFE_BOTS = [
    "betterdiscord", "powercord", "aliexpress", "nitro-steal",
    "token-grabber", "self-bot", "raid-bot", "spam-bot"
]

# قائمة الروابط الخبيثة
BAD_LINKS = [
    "discord.gift", "nitro-steal.com", "steamcheap.com", 
    "free-nitro.com", "discord-nitro.com", "hacknitro.com",
    "token-login", "steal-token"
]

# ========== نظام الاشتراكات ==========
subscriptions = {
    "trial": {"days": 3, "price": 0, "name": "تجريبي",
             "ar": "3 أيام مجانية", "en": "3 Days Free"},
    "monthly": {"days": 30, "price": 9.99, "name": "شهري",
               "ar": "شهر كامل", "en": "1 Month"},
    "yearly": {"days": 365, "price": 99.99, "name": "سنوي",
              "ar": "سنة كاملة (خصم 17%)", "en": "1 Year (17% off)"}
}

active_subscriptions = {}

# ========== الأحداث ==========
@bot.event
async def on_ready():
    print(f"✅ {bot.user} جاهز للحماية السيبرانية المتقدمة")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="الهجمات | حصين"))
    daily_report.start()
    print("📊 نظام التقارير اليومية مفعل")

@bot.event
async def on_member_join(member):
    now = datetime.now()
    
    join_tracker[member.guild.id].append({
        "time": now, 
        "member": member.name, 
        "id": member.id,
        "is_bot": member.bot
    })
    
    if member.bot:
        for unsafe in UNSAFE_BOTS:
            if unsafe in member.name.lower():
                bot_detection_tracker[member.guild.id].append({
                    "time": now,
                    "bot_name": member.name,
                    "bot_id": member.id,
                    "reason": f"مطابق لكلمة {unsafe}"
                })
                await member.kick(reason="بوت غير آمن")
    
    raid_tracker[member.guild.id].append(now)
    raid_tracker[member.guild.id] = [t for t in raid_tracker[member.guild.id] if (now - t).seconds < 10]
    
    if len(raid_tracker[member.guild.id]) > 5:
        attackers_tracker[member.guild.id].append({
            "time": now,
            "attacker": member.name,
            "attacker_id": member.id,
            "type": "Raid Attack"
        })
        await member.guild.edit(verification_level=discord.VerificationLevel.high)

@bot.event
async def on_member_remove(member):
    delete_tracker[member.guild.id].append({
        "time": datetime.now(), 
        "member": member.name, 
        "id": member.id
    })

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    for link in BAD_LINKS:
        if link in message.content.lower():
            await message.delete()
            suspicious_links_tracker[message.guild.id].append({
                "time": datetime.now(),
                "user": message.author.name,
                "user_id": message.author.id,
                "link": link
            })
            await message.channel.send(f"⚠️ {message.author.mention} تم حذف رابط خبيث")
            return
    
    now = datetime.now()
    if message.author.id not in spam_tracker:
        spam_tracker[message.author.id] = []
    
    spam_tracker[message.author.id] = [
        t for t in spam_tracker[message.author.id] 
        if (now - t["time"]).seconds < 5
    ]
    
    spam_tracker[message.author.id].append({
        "time": now,
        "content": message.content[:100],
        "channel": message.channel.name
    })
    
    if len(spam_tracker[message.author.id]) > 5:
        attackers_tracker[message.guild.id].append({
            "time": now,
            "attacker": message.author.name,
            "attacker_id": message.author.id,
            "type": "Spam Attack"
        })
        await message.author.timeout(timedelta(minutes=10))
        await message.channel.send(f"⚠️ {message.author.mention} تم كتمك بسبب السبام")
        return
    
    await process_commands_without_prefix(message)

async def process_commands_without_prefix(message):
    content = message.content.lower()
    
    if content in ["حصين", "protect", "حماية"]:
        await protect_command(message)
    elif content in ["تقرير", "report", "تقرير كامل", "full report"]:
        await advanced_report_command(message)
    elif content in ["اشتراك", "subscribe", "خطط", "plans"]:
        await subscription_command(message)
    elif content.startswith("تفعيل تجريبي") or content.startswith("activate trial"):
        await activate_trial_command(message)
    elif content in ["قفل", "lock"]:
        await lock_command(message)
    elif content in ["فتح", "unlock"]:
        await unlock_command(message)
    else:
        await bot.process_commands(message)

# ========== التقرير المتقدم ==========
async def advanced_report_command(message):
    if not message.author.guild_permissions.administrator:
        await message.channel.send("❌ Admin only")
        return
    
    embed = discord.Embed(
        title="🛡️ CYBER SECURITY INTELLIGENCE REPORT",
        description=f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                   f"**Server:** {message.guild.name}\n"
                   f"**Reported by:** {message.author.name}",
        color=0xff4444,
        timestamp=datetime.now()
    )
    
    guild_attacks = attackers_tracker.get(message.guild.id, [])
    recent_attacks = [a for a in guild_attacks if (datetime.now() - a["time"]).seconds < 3600]
    
    attackers_list = "\n".join([f"🔴 {a['attacker']} - {a['type']} at {a['time'].strftime('%H:%M:%S')}" 
                                for a in recent_attacks[-10:]]) or "✅ No attacks detected"
    
    embed.add_field(
        name="🚨 ATTACKERS & THREATS",
        value=f"```{attackers_list}```",
        inline=False
    )
    
    guild_bots = bot_detection_tracker.get(message.guild.id, [])
    bots_list = "\n".join([f"🤖 {b['bot_name']} - {b['reason']}" 
                           for b in guild_bots[-10:]]) or "✅ No suspicious bots detected"
    
    embed.add_field(
        name="⚠️ UNSAFE BOTS DETECTED",
        value=f"```{bots_list}```",
        inline=False
    )
    
    guild_links = suspicious_links_tracker.get(message.guild.id, [])
    links_list = "\n".join([f"🔗 {l['user']} tried: {l['link']}" 
                            for l in guild_links[-10:]]) or "✅ No malicious links detected"
    
    embed.add_field(
        name="🔗 MALICIOUS LINKS BLOCKED",
        value=f"```{links_list}```",
        inline=False
    )
    
    total_joins = len(join_tracker.get(message.guild.id, []))
    total_leaves = len(delete_tracker.get(message.guild.id, []))
    total_raids = len([r for r in raid_tracker.get(message.guild.id, []) if (datetime.now() - r).seconds < 60])
    
    embed.add_field(
        name="📊 STATISTICS",
        value=f"```\n• New Members: {total_joins}\n• Left Members: {total_leaves}\n• Raid Attempts: {total_raids}\n• Spam Violations: {len(spam_tracker)}\n• Suspicious Bots: {len(guild_bots)}\n• Malicious Links: {len(guild_links)}\n```",
        inline=False
    )
    
    embed.set_footer(text=f"CyberGuard Security System | Developed by {DEV_NAME}")
    
    await message.channel.send(embed=embed)

# ========== نظام الاشتراكات ==========
async def subscription_command(message):
    embed = discord.Embed(
        title="💎 CYBER SECURITY SUBSCRIPTION",
        description=f"**Developer:** {DEV_NAME}\n"
                   f"**Contact:** DM `{DEV_NAME}` on Discord",
        color=0x9b59b6
    )
    
    embed.add_field(
        name="🎁 TRIAL | تجريبي",
        value=f"```\n• Duration: 3 Days Free\n• Price: FREE\n• Code: تفعيل تجريبي\n```",
        inline=False
    )
    
    embed.add_field(
        name="📅 MONTHLY | شهري",
        value=f"```\n• Duration: 1 Month\n• Price: $9.99 USD\n• Full Protection\n```",
        inline=False
    )
    
    embed.add_field(
        name="🌟 YEARLY | سنوي",
        value=f"```\n• Duration: 1 Year\n• Price: $99.99 USD\n• Save 17% + VIP Support\n```",
        inline=False
    )
    
    embed.add_field(
        name="✅ HOW TO ACTIVATE",
        value=f"```\n1. Contact {DEV_NAME} on Discord\n2. Choose your plan\n3. Make payment\n4. Bot will be activated\n```",
        inline=False
    )
    
    embed.set_footer(text=f"CyberGuard Security | {DEV_NAME}")
    await message.channel.send(embed=embed)

async def activate_trial_command(message):
    if not message.author.guild_permissions.administrator:
        await message.channel.send("❌ Admin only")
        return
    
    guild_id = message.guild.id
    
    if guild_id in active_subscriptions:
        existing = active_subscriptions[guild_id]
        if existing["end_date"] > datetime.now():
            await message.channel.send("⚠️ Server already has an active subscription")
            return
    
    end_date = datetime.now() + timedelta(days=3)
    active_subscriptions[guild_id] = {
        "end_date": end_date,
        "plan": "trial",
        "activated_by": message.author.name
    }
    
    embed = discord.Embed(
        title="✅ TRIAL ACTIVATED",
        description=f"**Server:** {message.guild.name}\n"
                   f"**Duration:** 3 Days\n"
                   f"**Expires:** {end_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
                   f"**Activated by:** {message.author.name}",
        color=0x00ff00
    )
    embed.set_footer(text=f"Contact {DEV_NAME} to upgrade")
    await message.channel.send(embed=embed)

# ========== الأوامر الأساسية ==========
async def protect_command(message):
    if message.author.guild_permissions.administrator:
        embed = discord.Embed(
            title="🛡️ CYBER SECURITY SHIELD",
            description="Cyber Protection Activated",
            color=0x00ff00
        )
        embed.add_field(name="🚨 Anti-Raid", value="✅ Active", inline=True)
        embed.add_field(name="📝 Anti-Spam", value="✅ Active", inline=True)
        embed.add_field(name="🔗 Anti-Malware", value="✅ Active", inline=True)
        embed.add_field(name="🤖 Anti-Bot", value="✅ Active", inline=True)
        embed.add_field(name="📊 Daily Report", value="✅ Active", inline=True)
        embed.set_footer(text=f"CyberGuard Security | Developed by {DEV_NAME}")
        await message.channel.send(embed=embed)
    else:
        await message.channel.send("❌ Admin only")

async def lock_command(message):
    if message.author.guild_permissions.administrator:
        await message.channel.set_permissions(message.guild.default_role, send_messages=False)
        await message.channel.send("🔒 Channel Locked")
    else:
        await message.channel.send("❌ Admin only")

async def unlock_command(message):
    if message.author.guild_permissions.administrator:
        await message.channel.set_permissions(message.guild.default_role, send_messages=None)
        await message.channel.send("🔓 Channel Unlocked")
    else:
        await message.channel.send("❌ Admin only")

# ========== التقرير اليومي التلقائي ==========
@tasks.loop(hours=24)
async def daily_report():
    await asyncio.sleep(10)
    
    global report_channel_id
    
    if report_channel_id is None:
        for guild in bot.guilds:
            for channel in guild.text_channels:
                if channel.name in ["reports", "logs", "تقرير", "تقارير", "security"]:
                    report_channel_id = channel.id
                    break
            if report_channel_id:
                break
    
    if report_channel_id:
        channel = bot.get_channel(report_channel_id)
        if channel:
            total_attacks = sum(len(v) for v in attackers_tracker.values())
            total_bots = sum(len(v) for v in bot_detection_tracker.values())
            total_links = sum(len(v) for v in suspicious_links_tracker.values())
            
            embed = discord.Embed(
                title="📊 DAILY SECURITY INTELLIGENCE REPORT",
                description=f"**Date:** {datetime.now().strftime('%Y-%m-%d')}\n"
                           f"**Developer:** {DEV_NAME}",
                color=0xff4444
            )
            
            embed.add_field(name="🚨 Total Attacks", value=f"`{total_attacks}`", inline=True)
            embed.add_field(name="🤖 Suspicious Bots", value=f"`{total_bots}`", inline=True)
            embed.add_field(name="🔗 Malicious Links", value=f"`{total_links}`", inline=True)
            embed.add_field(name="🛡️ Protected Servers", value=f"`{len(bot.guilds)}`", inline=True)
            
            embed.set_footer(text=f"CyberGuard Security System | {DEV_NAME}")
            await channel.send(embed=embed)
    
    attackers_tracker.clear()
    bot_detection_tracker.clear()
    suspicious_links_tracker.clear()
    raid_tracker.clear()
    spam_tracker.clear()

@daily_report.before_loop
async def before_daily_report():
    await bot.wait_until_ready()

# ========== أوامر البادئة ==========
@bot.command(name="setreport", aliases=["تعيين_تقرير"])
@commands.has_permissions(administrator=True)
async def set_report_channel(ctx, channel: discord.TextChannel = None):
    global report_channel_id
    if channel is None:
        channel = ctx.channel
    report_channel_id = channel.id
    await ctx.send(f"✅ Report channel set to: {channel.mention}")

@bot.command(name="protect", aliases=["حصين", "حماية"])
@commands.has_permissions(administrator=True)
async def cmd_protect(ctx):
    await protect_command(ctx.message)

@bot.command(name="report", aliases=["تقرير"])
@commands.has_permissions(administrator=True)
async def cmd_report(ctx):
    await advanced_report_command(ctx.message)

@bot.command(name="subscribe", aliases=["اشتراك", "خطط"])
async def cmd_subscribe(ctx):
    await subscription_command(ctx.message)

@bot.command(name="lock", aliases=["قفل"])
@commands.has_permissions(administrator=True)
async def cmd_lock(ctx):
    await lock_command(ctx.message)

@bot.command(name="unlock", aliases=["فتح"])
@commands.has_permissions(administrator=True)
async def cmd_unlock(ctx):
    await unlock_command(ctx.message)

# ========== تشغيل البوت ==========
if TOKEN:
    bot.run(TOKEN)
else:
    print("⚠️ التوكن غير موجود. أضف DISCORD_TOKEN في ملف .env")