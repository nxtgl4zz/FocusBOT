import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, timedelta
import os
import pytz
from dotenv import load_dotenv
from models import init_db, get_db, close_db, UserStats, FocusSession
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

# Load environment variables
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

focus_sessions = {}  # {guild_id: {"members": set(), "end_time": datetime, "creator": user, "duration": int, "session_id": int}}

# Paris timezone
PARIS_TZ = pytz.timezone('Europe/Paris')

def get_paris_time():
    """Get current time in Paris timezone"""
    return datetime.now(PARIS_TZ)

def utc_to_paris(utc_dt):
    """Convert UTC datetime to Paris time"""
    if utc_dt.tzinfo is None:
        utc_dt = pytz.utc.localize(utc_dt)
    return utc_dt.astimezone(PARIS_TZ)

# Helper functions for database operations
async def save_session_stats(session_data, status="completed"):
    """Save session statistics to database"""
    db = get_db()
    try:
        # Update session record
        if "session_id" in session_data and session_data["session_id"]:
            db.query(FocusSession).filter(FocusSession.id == session_data["session_id"]).update({
                FocusSession.ended_at: datetime.utcnow(),
                FocusSession.status: status,
                FocusSession.participant_count: len(session_data["members"])
            })
        
        # Update user statistics
        for member in session_data["members"]:
            user_id = member.id if hasattr(member, 'id') else member
            username = member.display_name if hasattr(member, 'display_name') else str(user_id)
            
            user_stat = db.query(UserStats).filter(UserStats.user_id == user_id).first()
            if not user_stat:
                user_stat = UserStats(
                    user_id=user_id,
                    username=username,
                    total_minutes=session_data["duration"],
                    sessions_completed=1
                )
                db.add(user_stat)
            else:
                db.query(UserStats).filter(UserStats.user_id == user_id).update({
                    UserStats.total_minutes: UserStats.total_minutes + session_data["duration"],
                    UserStats.sessions_completed: UserStats.sessions_completed + 1,
                    UserStats.username: username,
                    UserStats.last_session: datetime.utcnow(),
                    UserStats.updated_at: datetime.utcnow()
                })
        
        db.commit()
    except Exception as e:
        print(f"Error saving session stats: {e}")
        db.rollback()
    finally:
        close_db(db)

def get_user_stats(user_id):
    """Get user statistics from database"""
    db = get_db()
    try:
        user_stat = db.query(UserStats).filter(UserStats.user_id == user_id).first()
        return user_stat
    finally:
        close_db(db)

def get_leaderboard(limit=10):
    """Get top users by focus time"""
    db = get_db()
    try:
        top_users = db.query(UserStats).order_by(desc(UserStats.total_minutes)).limit(limit).all()
        return top_users
    finally:
        close_db(db)

@tasks.loop(seconds=60)
async def cleanup_expired_sessions():
    """Automatically clean up expired sessions every minute"""
    current_time = datetime.utcnow()
    expired_guilds = []
    
    for guild_id, session in focus_sessions.items():
        if current_time >= session["end_time"]:
            expired_guilds.append(guild_id)
            # Notify the guild that the session ended
            guild = bot.get_guild(guild_id)
            if guild:
                # Find a channel to send the message (preferably the last active channel)
                channel = discord.utils.get(guild.text_channels, name='general')
                if not channel:
                    channel = guild.text_channels[0] if guild.text_channels else None
                
                if channel:
                    try:
                        await channel.send("⏰ La session de focus est terminée ! Bien joué à tous 🎉")
                    except discord.Forbidden:
                        pass  # Bot doesn't have permission to send messages
    
    # Remove expired sessions
    for guild_id in expired_guilds:
        # Save completed session statistics to database
        session_data = focus_sessions[guild_id]
        await save_session_stats(session_data, "completed")
        del focus_sessions[guild_id]

@bot.event
async def on_ready():
    print(f"✅ FocusBot connecté en tant que {bot.user}")
    init_db()  # Initialize database tables
    cleanup_expired_sessions.start()

@bot.command(name='startfocus')
async def start_focus(ctx, minutes: int):
    """Start a focus session for specified minutes (1-480 max)"""
    guild_id = ctx.guild.id
    
    # Validation
    if minutes < 1 or minutes > 480:
        await ctx.send("⚠️ La durée doit être entre 1 et 480 minutes (8 heures maximum).")
        return
    
    if guild_id in focus_sessions:
        end_time = focus_sessions[guild_id]["end_time"]
        time_left = end_time - datetime.utcnow()
        if time_left.total_seconds() > 0:
            minutes_left = int(time_left.total_seconds() / 60)
            await ctx.send(f"⚠️ Une session de focus est déjà en cours ! {minutes_left} minutes restantes.")
            return
    
    end_time = datetime.utcnow() + timedelta(minutes=minutes)
    
    # Create session record in database (optional, continue if fails)
    session_id = None
    try:
        db = get_db()
        session_record = FocusSession(
            guild_id=guild_id,
            creator_id=ctx.author.id,
            duration_minutes=minutes,
            participant_count=1
        )
        db.add(session_record)
        db.commit()
        session_id = session_record.id
        close_db(db)
    except Exception as e:
        print(f"Warning: Could not save session to database: {e}")
        if 'db' in locals():
            try:
                db.rollback()
                close_db(db)
            except:
                pass
    
    focus_sessions[guild_id] = {
        "members": {ctx.author}, 
        "end_time": end_time, 
        "creator": ctx.author,
        "duration": minutes,
        "session_id": session_id
    }
    
    # Convert end time to Paris timezone for display
    end_time_paris = utc_to_paris(end_time)
    end_time_str = end_time_paris.strftime('%H:%M (Paris)')
    await ctx.send(f"🧠 Session de focus lancée pour {minutes} minutes par {ctx.author.mention} ! "
                  f"Rejoignez avec `/joinfocus`. Fin prévue à {end_time_str} 🕒")

@bot.command(name='joinfocus')
async def join_focus(ctx):
    """Join the current focus session"""
    guild_id = ctx.guild.id
    
    if guild_id not in focus_sessions:
        await ctx.send("⚠️ Aucune session de focus en cours. Lancez-en une avec `/startfocus <minutes>`.")
        return
    
    # Check if session is still active
    current_time = datetime.utcnow()
    if current_time >= focus_sessions[guild_id]["end_time"]:
        del focus_sessions[guild_id]
        await ctx.send("⚠️ La session de focus vient de se terminer. Lancez-en une nouvelle avec `/startfocus <minutes>`.")
        return
    
    if ctx.author in focus_sessions[guild_id]["members"]:
        await ctx.send(f"✅ {ctx.author.mention} vous participez déjà à cette session de focus !")
        return
    
    focus_sessions[guild_id]["members"].add(ctx.author)
    end_time_paris = utc_to_paris(focus_sessions[guild_id]["end_time"])
    end_time_str = end_time_paris.strftime('%H:%M (Paris)')
    member_count = len(focus_sessions[guild_id]["members"])
    
    await ctx.send(f"✅ {ctx.author.mention} a rejoint la session de focus ! "
                  f"({member_count} participants) Fin prévue à {end_time_str}.")

@bot.command(name='leavefocus')
async def leave_focus(ctx):
    """Leave the current focus session"""
    guild_id = ctx.guild.id
    
    if guild_id not in focus_sessions:
        await ctx.send("⚠️ Aucune session de focus en cours.")
        return
    
    if ctx.author not in focus_sessions[guild_id]["members"]:
        await ctx.send("⚠️ Vous ne participez pas à la session de focus actuelle.")
        return
    
    focus_sessions[guild_id]["members"].remove(ctx.author)
    member_count = len(focus_sessions[guild_id]["members"])
    
    await ctx.send(f"👋 {ctx.author.mention} a quitté la session de focus. "
                  f"({member_count} participants restants)")
    
    # If no members left, end the session
    if member_count == 0:
        del focus_sessions[guild_id]
        await ctx.send("📪 Session de focus terminée - plus aucun participant.")

@bot.command(name='status')
async def focus_status(ctx):
    """Display current focus session status"""
    guild_id = ctx.guild.id
    
    if guild_id not in focus_sessions:
        await ctx.send("💤 Aucune session de focus en cours sur ce serveur.")
        return
    
    session = focus_sessions[guild_id]
    current_time = datetime.utcnow()
    
    # Check if session expired
    if current_time >= session["end_time"]:
        del focus_sessions[guild_id]
        await ctx.send("⏰ La session de focus vient de se terminer !")
        return
    
    time_left = session["end_time"] - current_time
    minutes_left = int(time_left.total_seconds() / 60)
    seconds_left = int(time_left.total_seconds() % 60)
    
    members_list = [member.mention for member in session["members"]]
    members_text = ", ".join(members_list)
    
    embed = discord.Embed(
        title="🧠 Session de Focus en Cours",
        color=0x00ff00,
        timestamp=datetime.utcnow()
    )
    
    embed.add_field(
        name="⏰ Temps restant", 
        value=f"{minutes_left}m {seconds_left}s", 
        inline=True
    )
    
    embed.add_field(
        name="👥 Participants", 
        value=f"{len(session['members'])}", 
        inline=True
    )
    
    embed.add_field(
        name="🚀 Créateur", 
        value=session["creator"].mention, 
        inline=True
    )
    
    embed.add_field(
        name="📝 Liste des participants", 
        value=members_text if members_text else "Aucun", 
        inline=False
    )
    
    end_time_paris = utc_to_paris(session["end_time"])
    end_time_str = end_time_paris.strftime('%H:%M (Paris)')
    embed.add_field(
        name="🏁 Fin prévue", 
        value=end_time_str, 
        inline=True
    )
    
    await ctx.send(embed=embed)

@bot.command(name='endfocus')
async def end_focus(ctx):
    """End the current focus session (creator or moderators only)"""
    guild_id = ctx.guild.id
    
    if guild_id not in focus_sessions:
        await ctx.send("⚠️ Aucune session de focus active à interrompre.")
        return
    
    session = focus_sessions[guild_id]
    
    # Check permissions: creator or user with manage_messages permission
    if ctx.author != session["creator"] and not ctx.author.guild_permissions.manage_messages:
        await ctx.send("⚠️ Seul le créateur de la session ou un modérateur peut l'interrompre.")
        return
    
    participant_count = len(session["members"])
    
    # Save session as cancelled
    await save_session_stats(session, "cancelled")
    del focus_sessions[guild_id]
    
    await ctx.send(f"❌ {ctx.author.mention} a mis fin à la session de focus. "
                  f"({participant_count} participants) Reposez-vous bien ! 💤")

@bot.command(name='mystats')
async def my_stats(ctx):
    """Display personal focus statistics"""
    user_stats = get_user_stats(ctx.author.id)
    
    if not user_stats:
        await ctx.send(f"📊 {ctx.author.mention}, tu n'as pas encore de statistiques de focus. "
                      f"Lance ta première session avec `/startfocus <minutes>` !")
        return
    
    total_minutes = user_stats.total_minutes
    hours = total_minutes // 60
    minutes = total_minutes % 60
    sessions = user_stats.sessions_completed
    
    # Calculate weekly stats (last 7 days)
    db = get_db()
    try:
        week_start = datetime.utcnow() - timedelta(days=7)
        weekly_sessions = db.query(FocusSession).filter(
            FocusSession.creator_id == ctx.author.id,
            FocusSession.started_at >= week_start,
            FocusSession.status == "completed"
        ).all()
        
        weekly_minutes = sum(session.duration_minutes for session in weekly_sessions)
        weekly_hours = weekly_minutes // 60
        weekly_mins = weekly_minutes % 60
    finally:
        close_db(db)
    
    embed = discord.Embed(
        title="📊 Tes Statistiques de Focus",
        color=0x00ff00,
        timestamp=get_paris_time()
    )
    
    embed.add_field(
        name="🧠 Total Focus",
        value=f"**{hours}h {minutes}min**",
        inline=True
    )
    
    embed.add_field(
        name="🔥 Sessions Complétées",
        value=f"**{sessions}** sessions",
        inline=True
    )
    
    embed.add_field(
        name="📅 Cette Semaine",
        value=f"**{weekly_hours}h {weekly_mins}min**",
        inline=True
    )
    
    if hours >= 10:
        embed.add_field(
            name="💪 Motivation",
            value="Tu as travaillé plus de 10 heures en mode focus, boss 👊",
            inline=False
        )
    elif weekly_hours >= 5:
        embed.add_field(
            name="🚀 Motivation",
            value="Excellente semaine de focus ! Continue comme ça 🔥",
            inline=False
        )
    
    embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else None)
    await ctx.send(embed=embed)

@bot.command(name='leaderboard')
async def leaderboard(ctx):
    """Display server focus leaderboard"""
    top_users = get_leaderboard(10)
    
    if not top_users:
        await ctx.send("📉 Aucun score de focus enregistré pour le moment. "
                      "Lance ta première session avec `/startfocus <minutes>` !")
        return
    
    embed = discord.Embed(
        title="🏆 Leaderboard Focus - Qui est le plus concentré ?",
        color=0xffd700,  # Gold color
        timestamp=get_paris_time()
    )
    
    description = ""
    medals = ["🥇", "🥈", "🥉"]
    
    for i, user_stat in enumerate(top_users, start=1):
        hours = user_stat.total_minutes // 60
        minutes = user_stat.total_minutes % 60
        
        medal = medals[i-1] if i <= 3 else f"**{i}.**"
        username = getattr(user_stat, 'username', None) or f"User#{user_stat.user_id}"
        
        description += f"{medal} {username} — {hours}h {minutes}min ({user_stat.sessions_completed} sessions)\n"
    
    embed.description = description
    
    # Add stats summary
    total_users = len(top_users)
    total_focus_time = sum(user.total_minutes for user in top_users)
    total_hours = total_focus_time // 60
    
    embed.add_field(
        name="📈 Statistiques du Serveur",
        value=f"**{total_users}** utilisateurs actifs\n**{total_hours}h** de focus total",
        inline=False
    )
    
    await ctx.send(embed=embed)

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Argument manquant. Utilisez `/startfocus <minutes>` (exemple: `/startfocus 25`)")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("⚠️ Veuillez fournir un nombre valide de minutes.")
    elif isinstance(error, commands.CommandNotFound):
        return  # Ignore unknown commands
    else:
        print(f"Erreur: {error}")

# Get token from environment or use placeholder
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not TOKEN:
    print("⚠️ DISCORD_BOT_TOKEN non trouvé dans les variables d'environnement")
    print("💡 Créez un fichier .env avec votre token: DISCORD_BOT_TOKEN=votre_token_ici")
    TOKEN = "YOUR_BOT_TOKEN_HERE"

if __name__ == "__main__":
    bot.run(TOKEN)
