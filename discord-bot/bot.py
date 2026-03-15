import discord
from discord.ext import commands, tasks
from discord import app_commands
import configparser
import json
import aiohttp
import asyncio
from datetime import datetime, timedelta
import os
from typing import Optional, Literal

# ==================== تحميل الإعدادات ====================
config = configparser.ConfigParser()
config.read('config.ini')

TOKEN = config['DISCORD']['token']
GUILD_ID = int(config['DISCORD']['guild_id'])
OWNER_ID = int(config['OWNER']['id'])
WEBHOOK_URL = config['WEBHOOK']['url']

# ==================== إعدادات البوت ====================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# ==================== هيكل البيانات ====================
DATA_FILE = 'factions_data.json'

factions_data = {
    'resistance': {
        'jenin': {'name': 'كتيبة جنين', 'leader': 'أبو محمد', 'members': []},
        'hamas': {'name': 'كتيبة حماس', 'leader': 'أبو العز', 'members': []},
        'lion': {'name': 'عرين الأسود', 'leader': 'أسد', 'members': []}
    },
    'server': {
        'occupation': {'name': 'جيش الاحتلال', 'leader': 'جنرال', 'members': []},
        'police': {'name': 'الشرطة الفلسطينية', 'leader': 'عقيد', 'members': []},
        'yamam': {'name': 'وحدة اليمام', 'leader': 'قائد', 'members': []},
        'occPolice': {'name': 'شرطة الاحتلال', 'leader': 'ضابط', 'members': []},
        'ambulance': {'name': 'اسعاف الاحتلال', 'leader': 'مسعف', 'members': []},
        'mechanic': {'name': 'الميكانيك', 'leader': 'مهندس', 'members': []}
    },
    'blacklist': [],
    'resignations': [],
    'vacations': [],
    'warnings': [],
    'logs': []
}

# ==================== دوال البيانات ====================
def load_data():
    """تحميل البيانات من ملف JSON"""
    global factions_data
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                # دمج البيانات مع الاحتفاظ بالهيكل
                for key in factions_data:
                    if key in saved:
                        if isinstance(factions_data[key], dict) and isinstance(saved[key], dict):
                            factions_data[key].update(saved[key])
                        else:
                            factions_data[key] = saved[key]
            print(f"✅ تم تحميل البيانات من {DATA_FILE}")
        except Exception as e:
            print(f"❌ خطأ في تحميل البيانات: {e}")

def save_data():
    """حفظ البيانات إلى ملف JSON"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(factions_data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"❌ خطأ في حفظ البيانات: {e}")
        return False

def add_log(action, user, details):
    """إضافة سجل حدث"""
    factions_data['logs'].append({
        'action': action,
        'user': str(user),
        'details': details,
        'time': datetime.now().isoformat()
    })
    if len(factions_data['logs']) > 100:
        factions_data['logs'] = factions_data['logs'][-100:]
    save_data()

# ==================== دوال Webhook ====================
async def send_to_webhook(embed):
    """إرسال إشعار إلى Webhook"""
    if not WEBHOOK_URL or WEBHOOK_URL == 'YOUR_WEBHOOK_URL_HERE':
        return
    
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(WEBHOOK_URL, json={
                'embeds': [embed]
            })
    except:
        pass

# ==================== حدث التشغيل ====================
@bot.event
async def on_ready():
    print(f'✅ {bot.user} متصل!')
    print(f'🆔 ID: {bot.user.id}')
    
    load_data()
    await bot.change_presence(activity=discord.Game(name="!اوامر | BLACK DEATH"))
    
    try:
        synced = await bot.tree.sync()
        print(f"✅ تم مزامنة {len(synced)} أمر سلاش")
    except Exception as e:
        print(f"❌ خطأ في مزامنة الأوامر: {e}")
    
    auto_save.start()
    print("✅ بدأ الحفظ التلقائي")

# ==================== الحفظ التلقائي ====================
@tasks.loop(minutes=5)
async def auto_save():
    save_data()

# ==================== التحقق من الصلاحيات ====================
def is_owner():
    async def predicate(interaction: discord.Interaction):
        return interaction.user.id == OWNER_ID
    return app_commands.check(predicate)

def is_admin():
    async def predicate(interaction: discord.Interaction):
        if interaction.user.id == OWNER_ID:
            return True
        return interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)

# ==================== أوامر سلاش (الأفضل) ====================

# ---- أمر المساعدة الرئيسي ----
@bot.tree.command(name="اوامر", description="عرض جميع أوامر البوت")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📚 أوامر بوت BLACK DEATH",
        description="جميع الأوامر مقسمة حسب الفئة",
        color=0xff3366
    )
    
    embed.add_field(
        name="👥 **إدارة الأعضاء**",
        value="`/اضافة عضو` - إضافة عضو جديد\n"
              "`/تعديل عضو` - تعديل بيانات عضو\n"
              "`/حذف عضو` - حذف عضو\n"
              "`/عرض اعضاء` - عرض أعضاء فاكشن\n"
              "`/بحث عضو` - بحث عن عضو",
        inline=False
    )
    
    embed.add_field(
        name="📊 **الإحصائيات**",
        value="`/احصائيات` - إحصائيات عامة\n"
              "`/تقرير` - تقرير مفصل\n"
              "`/سجلات` - عرض آخر الأحداث",
        inline=False
    )
    
    embed.add_field(
        name="⚔️ **أوامر الفاكشنات**",
        value="`/فاكشن` - معلومات فاكشن\n"
              "`/نقل عضو` - نقل عضو بين فاكشنات\n"
              "`/تغيير حالة` - تغيير حالة عضو",
        inline=False
    )
    
    embed.add_field(
        name="⛔ **القوائم السوداء**",
        value="`/بلاك لست` - إضافة لبلاك لست\n"
              "`/الغاء بلاك` - إزالة من بلاك لست\n"
              "`/استقالة` - تسجيل استقالة\n"
              "`/اجازة` - تسجيل إجازة\n"
              "`/تحذير` - إضافة تحذير",
        inline=False
    )
    
    embed.add_field(
        name="⚙️ **أوامر الإدارة**",
        value="`/تعديل قائد` - تعديل قائد فاكشن\n"
              "`/حفظ` - حفظ البيانات يدوياً\n"
              "`/تحميل` - تحميل البيانات\n"
              "`/باك اب` - عمل نسخة احتياطية",
        inline=False
    )
    
    embed.set_footer(text="BLACK DEATH • نظام إدارة الفاكشنات")
    
    await interaction.response.send_message(embed=embed)

# ---- إضافة عضو ----
@bot.tree.command(name="اضافة_عضو", description="إضافة عضو جديد إلى فاكشن")
@app_commands.describe(
    الفاكشن="اختر الفاكشن",
    الاسم="اسم الشخصية",
    الايدي="ايدي الشخصية",
    الرتبة="الرتبة داخل الفاكشن",
    الحالة="حالة العضو"
)
@app_commands.choices(الفاكشن=[
    app_commands.Choice(name="كتيبة جنين", value="jenin"),
    app_commands.Choice(name="كتيبة حماس", value="hamas"),
    app_commands.Choice(name="عرين الأسود", value="lion"),
    app_commands.Choice(name="جيش الاحتلال", value="occupation"),
    app_commands.Choice(name="الشرطة الفلسطينية", value="police"),
    app_commands.Choice(name="وحدة اليمام", value="yamam"),
    app_commands.Choice(name="شرطة الاحتلال", value="occPolice"),
    app_commands.Choice(name="اسعاف الاحتلال", value="ambulance"),
    app_commands.Choice(name="الميكانيك", value="mechanic")
])
@app_commands.choices(الحالة=[
    app_commands.Choice(name="نشط", value="نشط"),
    app_commands.Choice(name="غير نشط", value="غير نشط"),
    app_commands.Choice(name="إجازة", value="إجازة")
])
@is_admin()
async def add_member(
    interaction: discord.Interaction,
    الفاكشن: str,
    الاسم: str,
    الايدي: str,
    الرتبة: str = "عضو",
    الحالة: str = "نشط"
):
    member = {
        'name': الاسم,
        'id': الايدي,
        'rank': الرتبة,
        'status': الحالة,
        'joinDate': datetime.now().isoformat(),
        'addedBy': str(interaction.user)
    }
    
    # تحديد مكان الإضافة
    if الفاكشن in ['jenin', 'hamas', 'lion']:
        factions_data['resistance'][الفاكشن]['members'].append(member)
        faction_name = factions_data['resistance'][الفاكشن]['name']
    else:
        factions_data['server'][الفاكشن]['members'].append(member)
        faction_name = factions_data['server'][الفاكشن]['name']
    
    save_data()
    add_log('➕ إضافة عضو', interaction.user, f'{الاسم} إلى {faction_name}')
    
    embed = discord.Embed(
        title="✅ تم إضافة العضو",
        color=0x28a745,
        timestamp=datetime.now()
    )
    embed.add_field(name="الفاكشن", value=faction_name, inline=True)
    embed.add_field(name="الاسم", value=الاسم, inline=True)
    embed.add_field(name="الايدي", value=الايدي, inline=True)
    embed.add_field(name="الرتبة", value=الرتبة, inline=True)
    embed.add_field(name="الحالة", value=الحالة, inline=True)
    
    await interaction.response.send_message(embed=embed)
    
    # إرسال Webhook
    await send_to_webhook(embed)

# ---- عرض الأعضاء ----
@bot.tree.command(name="عرض_اعضاء", description="عرض أعضاء فاكشن معين")
@app_commands.describe(الفاكشن="اختر الفاكشن")
@app_commands.choices(الفاكشن=[
    app_commands.Choice(name="كتيبة جنين", value="jenin"),
    app_commands.Choice(name="كتيبة حماس", value="hamas"),
    app_commands.Choice(name="عرين الأسود", value="lion"),
    app_commands.Choice(name="جيش الاحتلال", value="occupation"),
    app_commands.Choice(name="الشرطة الفلسطينية", value="police"),
    app_commands.Choice(name="وحدة اليمام", value="yamam"),
    app_commands.Choice(name="شرطة الاحتلال", value="occPolice"),
    app_commands.Choice(name="اسعاف الاحتلال", value="ambulance"),
    app_commands.Choice(name="الميكانيك", value="mechanic")
])
async def show_members(interaction: discord.Interaction, الفاكشن: str):
    if الفاكشن in ['jenin', 'hamas', 'lion']:
        faction = factions_data['resistance'][الفاكشن]
    else:
        faction = factions_data['server'][الفاكشن]
    
    if not faction['members']:
        await interaction.response.send_message("❌ لا يوجد أعضاء في هذا الفاكشن")
        return
    
    members_list = ""
    for i, member in enumerate(faction['members'][:20], 1):
        members_list += f"{i}. **{member['name']}** (#{member['id']}) - {member.get('rank', 'عضو')} [{member.get('status', 'نشط')}]\n"
    
    if len(faction['members']) > 20:
        members_list += f"\n...و {len(faction['members']) - 20} أعضاء آخرين"
    
    embed = discord.Embed(
        title=f"📋 أعضاء {faction['name']}",
        description=members_list,
        color=0xff3366
    )
    embed.set_footer(text=f"إجمالي الأعضاء: {len(faction['members'])}")
    
    await interaction.response.send_message(embed=embed)

# ---- حذف عضو ----
@bot.tree.command(name="حذف_عضو", description="حذف عضو من فاكشن")
@app_commands.describe(
    الفاكشن="اختر الفاكشن",
    الايدي="ايدي العضو"
)
@app_commands.choices(الفاكشن=[
    app_commands.Choice(name="كتيبة جنين", value="jenin"),
    app_commands.Choice(name="كتيبة حماس", value="hamas"),
    app_commands.Choice(name="عرين الأسود", value="lion"),
    app_commands.Choice(name="جيش الاحتلال", value="occupation"),
    app_commands.Choice(name="الشرطة الفلسطينية", value="police"),
    app_commands.Choice(name="وحدة اليمام", value="yamam"),
    app_commands.Choice(name="شرطة الاحتلال", value="occPolice"),
    app_commands.Choice(name="اسعاف الاحتلال", value="ambulance"),
    app_commands.Choice(name="الميكانيك", value="mechanic")
])
@is_admin()
async def delete_member(interaction: discord.Interaction, الفاكشن: str, الايدي: str):
    if الفاكشن in ['jenin', 'hamas', 'lion']:
        faction = factions_data['resistance'][الفاكشن]
    else:
        faction = factions_data['server'][الفاكشن]
    
    for i, member in enumerate(faction['members']):
        if member['id'] == الايدي:
            deleted = faction['members'].pop(i)
            save_data()
            add_log('🗑️ حذف عضو', interaction.user, f'{deleted["name"]}')
            
            await interaction.response.send_message(f"✅ تم حذف {deleted['name']} من {faction['name']}")
            return
    
    await interaction.response.send_message("❌ لم يتم العثور على العضو")

# ---- تعديل عضو ----
@bot.tree.command(name="تعديل_عضو", description="تعديل بيانات عضو")
@app_commands.describe(
    الفاكشن="اختر الفاكشن",
    الايدي="ايدي العضو",
    الاسم_الجديد="الاسم الجديد (اختياري)",
    الرتبة_الجديدة="الرتبة الجديدة (اختياري)",
    الحالة_الجديدة="الحالة الجديدة (اختياري)"
)
@app_commands.choices(الفاكشن=[
    app_commands.Choice(name="كتيبة جنين", value="jenin"),
    app_commands.Choice(name="كتيبة حماس", value="hamas"),
    app_commands.Choice(name="عرين الأسود", value="lion"),
    app_commands.Choice(name="جيش الاحتلال", value="occupation"),
    app_commands.Choice(name="الشرطة الفلسطينية", value="police"),
    app_commands.Choice(name="وحدة اليمام", value="yamam"),
    app_commands.Choice(name="شرطة الاحتلال", value="occPolice"),
    app_commands.Choice(name="اسعاف الاحتلال", value="ambulance"),
    app_commands.Choice(name="الميكانيك", value="mechanic")
])
@app_commands.choices(الحالة_الجديدة=[
    app_commands.Choice(name="نشط", value="نشط"),
    app_commands.Choice(name="غير نشط", value="غير نشط"),
    app_commands.Choice(name="إجازة", value="إجازة")
])
@is_admin()
async def edit_member(
    interaction: discord.Interaction,
    الفاكشن: str,
    الايدي: str,
    الاسم_الجديد: Optional[str] = None,
    الرتبة_الجديدة: Optional[str] = None,
    الحالة_الجديدة: Optional[str] = None
):
    if الفاكشن in ['jenin', 'hamas', 'lion']:
        faction = factions_data['resistance'][الفاكشن]
    else:
        faction = factions_data['server'][الفاكشن]
    
    for member in faction['members']:
        if member['id'] == الايدي:
            old_data = member.copy()
            
            if الاسم_الجديد:
                member['name'] = الاسم_الجديد
            if الرتبة_الجديدة:
                member['rank'] = الرتبة_الجديدة
            if الحالة_الجديدة:
                member['status'] = الحالة_الجديدة
            
            save_data()
            add_log('✏️ تعديل عضو', interaction.user, f'{member["name"]}')
            
            embed = discord.Embed(
                title="✅ تم تعديل العضو",
                color=0xff3366
            )
            embed.add_field(name="العضو", value=member['name'], inline=True)
            embed.add_field(name="الايدي", value=member['id'], inline=True)
            
            await interaction.response.send_message(embed=embed)
            return
    
    await interaction.response.send_message("❌ لم يتم العثور على العضو")

# ---- الإحصائيات ----
@bot.tree.command(name="احصائيات", description="عرض إحصائيات شاملة")
async def statistics(interaction: discord.Interaction):
    total = 0
    resistance_total = 0
    server_total = 0
    active = 0
    
    for key in factions_data['resistance']:
        resistance_total += len(factions_data['resistance'][key]['members'])
        active += sum(1 for m in factions_data['resistance'][key]['members'] if m.get('status') == 'نشط')
    
    for key in factions_data['server']:
        server_total += len(factions_data['server'][key]['members'])
        active += sum(1 for m in factions_data['server'][key]['members'] if m.get('status') == 'نشط')
    
    total = resistance_total + server_total
    
    embed = discord.Embed(
        title="📊 إحصائيات الفاكشنات",
        color=0xff3366,
        timestamp=datetime.now()
    )
    
    embed.add_field(name="👥 إجمالي الأعضاء", value=str(total), inline=True)
    embed.add_field(name="✅ النشطاء", value=str(active), inline=True)
    embed.add_field(name="⚔️ المقاومة", value=str(resistance_total), inline=True)
    embed.add_field(name="🛡️ الخادم", value=str(server_total), inline=True)
    embed.add_field(name="⛔ بلاك لست", value=str(len(factions_data['blacklist'])), inline=True)
    embed.add_field(name="📝 استقالات", value=str(len(factions_data['resignations'])), inline=True)
    embed.add_field(name="🏖️ إجازات", value=str(len(factions_data['vacations'])), inline=True)
    embed.add_field(name="⚠️ تحذيرات", value=str(len(factions_data['warnings'])), inline=True)
    
    await interaction.response.send_message(embed=embed)

# ---- تقرير مفصل ----
@bot.tree.command(name="تقرير", description="تقرير مفصل عن فاكشن معين")
@app_commands.describe(الفاكشن="اختر الفاكشن")
@app_commands.choices(الفاكشن=[
    app_commands.Choice(name="كتيبة جنين", value="jenin"),
    app_commands.Choice(name="كتيبة حماس", value="hamas"),
    app_commands.Choice(name="عرين الأسود", value="lion"),
    app_commands.Choice(name="جيش الاحتلال", value="occupation"),
    app_commands.Choice(name="الشرطة الفلسطينية", value="police"),
    app_commands.Choice(name="وحدة اليمام", value="yamam"),
    app_commands.Choice(name="شرطة الاحتلال", value="occPolice"),
    app_commands.Choice(name="اسعاف الاحتلال", value="ambulance"),
    app_commands.Choice(name="الميكانيك", value="mechanic")
])
async def faction_report(interaction: discord.Interaction, الفاكشن: str):
    if الفاكشن in ['jenin', 'hamas', 'lion']:
        faction = factions_data['resistance'][الفاكشن]
    else:
        faction = factions_data['server'][الفاكشن]
    
    active = sum(1 for m in faction['members'] if m.get('status') == 'نشط')
    inactive = sum(1 for m in faction['members'] if m.get('status') == 'غير نشط')
    vacation = sum(1 for m in faction['members'] if m.get('status') == 'إجازة')
    
    embed = discord.Embed(
        title=f"📋 تقرير {faction['name']}",
        color=0xff3366
    )
    
    embed.add_field(name="👥 إجمالي الأعضاء", value=str(len(faction['members'])), inline=True)
    embed.add_field(name="✅ نشطاء", value=str(active), inline=True)
    embed.add_field(name="❌ غير نشطاء", value=str(inactive), inline=True)
    embed.add_field(name="🏖️ في إجازة", value=str(vacation), inline=True)
    embed.add_field(name="👑 القائد", value=faction['leader'], inline=True)
    
    if faction['members']:
        latest = faction['members'][-1]
        embed.add_field(name="🆕 آخر عضو", value=f"{latest['name']} (#{latest['id']})", inline=True)
    
    await interaction.response.send_message(embed=embed)

# ---- بلاك ليست ----
@bot.tree.command(name="بلاك_ليست", description="إضافة عضو إلى البلاك ليست")
@app_commands.describe(
    الاسم="اسم العضو",
    السبب="سبب الإضافة"
)
@is_admin()
async def add_blacklist(interaction: discord.Interaction, الاسم: str, السبب: str):
    item = {
        'name': الاسم,
        'reason': السبب,
        'addedBy': str(interaction.user),
        'date': datetime.now().isoformat()
    }
    
    factions_data['blacklist'].append(item)
    save_data()
    add_log('⛔ بلاك ليست', interaction.user, f'{الاسم} - {السبب}')
    
    embed = discord.Embed(
        title="⛔ تمت الإضافة إلى البلاك ليست",
        description=f"**الاسم:** {الاسم}\n**السبب:** {السبب}",
        color=0xff0000
    )
    
    await interaction.response.send_message(embed=embed)

# ---- استقالة ----
@bot.tree.command(name="استقالة", description="تسجيل استقالة عضو")
@app_commands.describe(
    الاسم="اسم العضو",
    الفاكشن="الفاكشن المستقيل منه",
    السبب="سبب الاستقالة"
)
@is_admin()
async def add_resignation(interaction: discord.Interaction, الاسم: str, الفاكشن: str, السبب: str):
    item = {
        'name': الاسم,
        'faction': الفاكشن,
        'reason': السبب,
        'date': datetime.now().isoformat()
    }
    
    factions_data['resignations'].append(item)
    save_data()
    add_log('📝 استقالة', interaction.user, f'{الاسم} من {الفاكشن}')
    
    embed = discord.Embed(
        title="📝 تم تسجيل الاستقالة",
        description=f"**الاسم:** {الاسم}\n**الفاكشن:** {الفاكشن}\n**السبب:** {السبب}",
        color=0xff9900
    )
    
    await interaction.response.send_message(embed=embed)

# ---- إجازة ----
@bot.tree.command(name="اجازة", description="تسجيل إجازة عضو")
@app_commands.describe(
    الاسم="اسم العضو",
    المدة="مدة الإجازة",
    السبب="سبب الإجازة"
)
@is_admin()
async def add_vacation(interaction: discord.Interaction, الاسم: str, المدة: str, السبب: str):
    item = {
        'name': الاسم,
        'duration': المدة,
        'reason': السبب,
        'date': datetime.now().isoformat()
    }
    
    factions_data['vacations'].append(item)
    save_data()
    add_log('🏖️ إجازة', interaction.user, f'{الاسم} - {المدة}')
    
    embed = discord.Embed(
        title="🏖️ تم تسجيل الإجازة",
        description=f"**الاسم:** {الاسم}\n**المدة:** {المدة}\n**السبب:** {السبب}",
        color=0x00ccff
    )
    
    await interaction.response.send_message(embed=embed)

# ---- تحذير ----
@bot.tree.command(name="تحذير", description="إضافة تحذير لعضو")
@app_commands.describe(
    الاسم="اسم العضو",
    السبب="سبب التحذير"
)
@is_admin()
async def add_warning(interaction: discord.Interaction, الاسم: str, السبب: str):
    item = {
        'name': الاسم,
        'reason': السبب,
        'addedBy': str(interaction.user),
        'date': datetime.now().isoformat()
    }
    
    factions_data['warnings'].append(item)
    save_data()
    add_log('⚠️ تحذير', interaction.user, f'{الاسم} - {السبب}')
    
    embed = discord.Embed(
        title="⚠️ تم إضافة تحذير",
        description=f"**الاسم:** {الاسم}\n**السبب:** {السبب}",
        color=0xffaa00
    )
    
    await interaction.response.send_message(embed=embed)

# ---- سجلات ----
@bot.tree.command(name="سجلات", description="عرض آخر 10 أحداث")
async def show_logs(interaction: discord.Interaction):
    if not factions_data['logs']:
        await interaction.response.send_message("📭 لا توجد سجلات")
        return
    
    logs_text = ""
    for log in factions_data['logs'][-10:]:
        time = datetime.fromisoformat(log['time']).strftime("%H:%M")
        logs_text += f"[{time}] {log['action']}: {log['details']}\n"
    
    embed = discord.Embed(
        title="📋 آخر الأحداث",
        description=logs_text,
        color=0xff3366
    )
    
    await interaction.response.send_message(embed=embed)

# ---- نقل عضو بين فاكشنات ----
@bot.tree.command(name="نقل_عضو", description="نقل عضو بين فاكشنات")
@app_commands.describe(
    الايدي="ايدي العضو",
    من_فاكشن="الفاكشن الحالي",
    الى_فاكشن="الفاكشن الجديد"
)
@app_commands.choices(من_فاكشن=[
    app_commands.Choice(name="كتيبة جنين", value="jenin"),
    app_commands.Choice(name="كتيبة حماس", value="hamas"),
    app_commands.Choice(name="عرين الأسود", value="lion"),
    app_commands.Choice(name="جيش الاحتلال", value="occupation"),
    app_commands.Choice(name="الشرطة الفلسطينية", value="police"),
    app_commands.Choice(name="وحدة اليمام", value="yamam"),
    app_commands.Choice(name="شرطة الاحتلال", value="occPolice"),
    app_commands.Choice(name="اسعاف الاحتلال", value="ambulance"),
    app_commands.Choice(name="الميكانيك", value="mechanic")
])
@app_commands.choices(الى_فاكشن=[
    app_commands.Choice(name="كتيبة جنين", value="jenin"),
    app_commands.Choice(name="كتيبة حماس", value="hamas"),
    app_commands.Choice(name="عرين الأسود", value="lion"),
    app_commands.Choice(name="جيش الاحتلال", value="occupation"),
    app_commands.Choice(name="الشرطة الفلسطينية", value="police"),
    app_commands.Choice(name="وحدة اليمام", value="yamam"),
    app_commands.Choice(name="شرطة الاحتلال", value="occPolice"),
    app_commands.Choice(name="اسعاف الاحتلال", value="ambulance"),
    app_commands.Choice(name="الميكانيك", value="mechanic")
])
@is_admin()
async def move_member(interaction: discord.Interaction, الايدي: str, من_فاكشن: str, الى_فاكشن: str):
    # البحث في الفاكشن المصدر
    if من_فاكشن in ['jenin', 'hamas', 'lion']:
        source = factions_data['resistance'][من_فاكشن]
    else:
        source = factions_data['server'][من_فاكشن]
    
    member = None
    for i, m in enumerate(source['members']):
        if m['id'] == الايدي:
            member = source['members'].pop(i)
            break
    
    if not member:
        await interaction.response.send_message("❌ لم يتم العثور على العضو")
        return
    
    # إضافة إلى الفاكشن الهدف
    if الى_فاكشن in ['jenin', 'hamas', 'lion']:
        factions_data['resistance'][الى_فاكشن]['members'].append(member)
        target_name = factions_data['resistance'][الى_فاكشن]['name']
    else:
        factions_data['server'][الى_فاكشن]['members'].append(member)
        target_name = factions_data['server'][الى_فاكشن]['name']
    
    save_data()
    add_log('🔄 نقل عضو', interaction.user, f'{member["name"]} إلى {target_name}')
    
    embed = discord.Embed(
        title="✅ تم نقل العضو",
        color=0x28a745
    )
    embed.add_field(name="العضو", value=member['name'], inline=True)
    embed.add_field(name="الفاكشن الجديد", value=target_name, inline=True)
    
    await interaction.response.send_message(embed=embed)

# ---- باك أب ----
@bot.tree.command(name="باك_اب", description="عمل نسخة احتياطية من البيانات")
@is_owner()
async def backup_data(interaction: discord.Interaction):
    # حفظ نسخة احتياطية
    backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(factions_data, f, ensure_ascii=False, indent=4)
    
    await interaction.response.send_message(
        content="✅ تم عمل نسخة احتياطية",
        file=discord.File(backup_file)
    )
    
    # حذف الملف بعد الإرسال
    os.remove(backup_file)

# ---- أوامر بسيطة ----
@bot.command(name='بنج')
async def ping(ctx):
    await ctx.send(f'🏓 البنج: {round(bot.latency * 1000)}ms')

@bot.command(name='احصائيات')
async def stats_simple(ctx):
    total = sum(len(f['members']) for f in factions_data['resistance'].values()) + \
            sum(len(f['members']) for f in factions_data['server'].values())
    
    embed = discord.Embed(
        title="📊 إحصائيات سريعة",
        description=f"إجمالي الأعضاء: {total}",
        color=0xff3366
    )
    await ctx.send(embed=embed)

# ==================== معالج الأخطاء ====================
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingRole):
        await interaction.response.send_message("❌ ليس لديك صلاحية لاستخدام هذا الأمر", ephemeral=True)
    elif isinstance(error, app_commands.errors.CheckFailure):
        await interaction.response.send_message("❌ هذا الأمر مخصص للمشرفين فقط", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ حدث خطأ: {error}", ephemeral=True)
        print(f"Error: {error}")

# ==================== تشغيل البوت ====================
if __name__ == "__main__":
    print("🤖 جاري تشغيل بوت BLACK DEATH...")
    bot.run(TOKEN)