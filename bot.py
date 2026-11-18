import discord
from discord.ext import commands
from discord import app_commands
import asyncio

# ══════════════════════════════════════════════
#  CONFIG — edit these
# ══════════════════════════════════════════════
BOT_TOKEN      = "MTU3MjUxOTM1NjExNjc3MDk0Nw.G-srQh.LXKXR2bWf1-UfAIk7UbhVWqU-n2HKoOGv6iGJs"
GUILD_ID       = 1564278474212900884   # your server ID
TICKET_CATEGORY= 1564517463947878421   # category ID where tickets go
SUPPORT_ROLE   = 1564287931630227456   # role ID that can see tickets
TICKET_CHANNEL = 1564517673545637998   # channel ID where the panel is sent

# ══════════════════════════════════════════════
#  BOT SETUP
# ══════════════════════════════════════════════
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ══════════════════════════════════════════════
#  PAYMENT METHOD SELECT
# ══════════════════════════════════════════════
class PaymentSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="PayPal",
                description="Pay via PayPal (USD)",
                emoji="🅿️"
            ),
            discord.SelectOption(
                label="GCash",
                description="Pay via GCash (PHP)",
                emoji="💚"
            ),
            discord.SelectOption(
                label="Robux",
                description="Pay via Robux (gamepass/group funds)",
                emoji="🟡"
            ),
        ]
        super().__init__(
            placeholder="Select your payment method",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        method = self.values[0]
        guild  = interaction.guild

        # Create ticket channel
        category = guild.get_channel(TICKET_CATEGORY)
        support  = guild.get_role(SUPPORT_ROLE)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user:   discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }
        if support:
            overwrites[support] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        ticket_name = f"ticket-{interaction.user.name}".lower().replace(" ", "-")
        ticket_ch   = await guild.create_text_channel(
            ticket_name,
            category=category,
            overwrites=overwrites,
            topic=f"Ticket for {interaction.user} | Payment: {method}"
        )

        # Payment method details
        method_info = {
            "PayPal": "💰 Send payment via **PayPal Friends & Family** (USD)\nPlease wait for a staff member to provide the PayPal address.",
            "GCash":  "💚 Send payment via **GCash** (PHP)\nPlease wait for a staff member to provide the GCash number.",
            "Robux":  "🟡 Send payment via **Robux** (Gamepass or Group Funds)\nPlease wait for a staff member to set up the gamepass.",
        }

        embed = discord.Embed(
            title="🎫 Ticket Opened",
            color=0x2b2b2b
        )
        embed.add_field(
            name="Customer",
            value=interaction.user.mention,
            inline=True
        )
        embed.add_field(
            name="Payment Method",
            value=method,
            inline=True
        )
        embed.add_field(
            name="📋 Instructions",
            value=method_info[method],
            inline=False
        )
        embed.set_footer(text="RAWS.CC | A staff member will assist you shortly.")

        mention = support.mention if support else "@Support"
        await ticket_ch.send(
            content=f"{interaction.user.mention} {mention}",
            embed=embed,
            view=CloseTicketView()
        )

        # Confirm to user (ephemeral)
        await interaction.response.send_message(
            f"✅ Ticket created! Head to {ticket_ch.mention}",
            ephemeral=True
        )
        self.disabled = True


class PaymentSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(PaymentSelect())


# ══════════════════════════════════════════════
#  CLOSE TICKET BUTTON
# ══════════════════════════════════════════════
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Closing ticket in 5 seconds...", ephemeral=False)
        await asyncio.sleep(5)
        await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")


# ══════════════════════════════════════════════
#  TICKET PANEL (the main embed)
# ══════════════════════════════════════════════
class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Select your payment method",
        style=discord.ButtonStyle.secondary,
        emoji="🛒",
        custom_id="open_ticket"
    )
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = PaymentSelectView()
        await interaction.response.send_message(
            "Choose how you want to pay:",
            view=view,
            ephemeral=True
        )


# ══════════════════════════════════════════════
#  SEND PANEL COMMAND
# ══════════════════════════════════════════════
@tree.command(name="panel", description="Send the RAWS ticket panel", guild=discord.Object(id=GUILD_ID))
async def panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="RAWS.CC — Tickets",
        color=0x1a1a1a
    )
    embed.add_field(
        name="💵 Price",
        value=(
            "╰• **Script:** $10 / 150 Robux / R$1000"
        ),
        inline=False
    )
    embed.add_field(
        name="💳 Payment Methods",
        value=(
            "╰• **PayPal** 🅿️\n"
            "╰• **GCash** 💚\n"
            "╰• **Robux** 🟡"
        ),
        inline=False
    )
    embed.set_footer(text="raws.cc | Click below to open a ticket")

    await interaction.channel.send(embed=embed, view=TicketPanelView())
    await interaction.response.send_message("✅ Panel sent!", ephemeral=True)


# ══════════════════════════════════════════════
#  ON READY
# ══════════════════════════════════════════════
@bot.event
async def on_ready():
    # Re-register persistent views so buttons work after restart
    bot.add_view(TicketPanelView())
    bot.add_view(CloseTicketView())
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"✅ Logged in as {bot.user} | Synced commands to guild {GUILD_ID}")


bot.run(BOT_TOKEN)
