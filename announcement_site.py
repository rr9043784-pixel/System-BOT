import os
import json
import secrets
import asyncio
import logging
import sys
import time
import random
from datetime import datetime, timezone, timedelta
import urllib.parse
import urllib.request
import urllib.error

import discord
from discord import app_commands
from flask import request, session, redirect, jsonify, render_template_string

logger = logging.getLogger(__name__)

OWNER_ID = 1176149190192152626

CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")

REDIRECT_URI = os.getenv(
    "DISCORD_REDIRECT_URI",
    "https://system-bot-production-1021.up.railway.app/announcement/callback"
)

BASE_URL = os.getenv(
    "ANNOUNCEMENT_BASE_URL",
    "https://system-bot-production-1021.up.railway.app"
).rstrip("/")

DISCORD_API = "https://discord.com/api/v10"


HTML = r"""
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>System-BOT Dashboard</title>
<style>
:root{--bg:#090d16;--panel:#111827;--panel2:#0d1421;--line:#253149;--muted:#91a0b8;--text:#edf2ff;--accent:#6875ff;--accent2:#8b5cf6;--green:#36c98f;--red:#f06b7b}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px Inter,Arial,sans-serif}button,input,select,textarea{font:inherit}header{height:66px;padding:0 24px;background:#0c1220;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:5}.brand{font-size:17px;font-weight:900;letter-spacing:.4px}.brand span{color:#8290ff}.topright{display:flex;gap:14px;align-items:center;color:var(--muted)}a{color:#b7c3ff;text-decoration:none}.layout{display:grid;grid-template-columns:235px minmax(0,1fr);min-height:calc(100vh - 66px)}aside{background:#0c1220;border-right:1px solid var(--line);padding:20px 13px}.navlabel{font-size:10px;color:#66748d;font-weight:800;letter-spacing:1.3px;padding:13px 12px 7px}.nav{display:flex;width:100%;text-align:left;border:0;background:transparent;color:#aebbd1;padding:11px 12px;border-radius:9px;cursor:pointer;margin:2px 0}.nav:hover,.nav.active{background:#1b2540;color:white}.nav.active{box-shadow:inset 3px 0 #7784ff}.main{padding:26px;max-width:1450px;width:100%;margin:auto}.head{display:flex;justify-content:space-between;align-items:flex-start;gap:18px;margin-bottom:22px}.head h1{font-size:27px;margin:0 0 7px}.muted{color:var(--muted)}.guildbox{min-width:220px}.card{background:var(--panel);border:1px solid var(--line);border-radius:13px;padding:19px;margin-bottom:17px}.card h2{font-size:16px;margin:0 0 15px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.grid3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:13px}.stat{background:linear-gradient(145deg,#17213a,#111827);border:1px solid var(--line);border-radius:12px;padding:17px}.stat b{display:block;font-size:25px;margin-top:9px}.stat small{color:var(--muted)}label{display:block;color:#aebbd1;font-size:12px;margin:12px 0 7px}input,select,textarea{width:100%;background:#090f1b;color:#f5f7ff;border:1px solid #303d56;border-radius:8px;padding:11px;outline:none}input:focus,select:focus,textarea:focus{border-color:var(--accent)}textarea{min-height:95px;resize:vertical}.btn{border:0;background:linear-gradient(100deg,#5968ef,#7858d8);color:white;border-radius:8px;padding:10px 15px;font-weight:700;cursor:pointer;margin:7px 5px 0 0}.btn.secondary{background:#26334c}.btn.danger{background:#9e394b}.btn.success{background:#197d61}.btn:disabled{opacity:.5;cursor:wait}.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.row>*{flex:1}.tablewrap{overflow:auto}table{width:100%;border-collapse:collapse;min-width:520px}th,td{text-align:left;padding:11px;border-bottom:1px solid var(--line);vertical-align:top}th{font-size:11px;text-transform:uppercase;color:#8998b1}td{color:#dce4f4}.pill{display:inline-block;padding:4px 8px;border-radius:20px;background:#222e49;color:#bdc9ff;font-size:11px}.pill.good{background:#143b33;color:#79e2ba}.pill.bad{background:#49232e;color:#ff9cac}.hidden{display:none!important}.status{margin:12px 0;color:#a9b8d0;white-space:pre-wrap}.notice{padding:12px;background:#171f31;border:1px solid var(--line);border-radius:8px;color:#aebbd1}.check{display:flex;gap:9px;align-items:center;margin:12px 0}.check input{width:auto}.colorrow{display:flex;gap:9px}.colorrow input[type=color]{width:60px;padding:3px}.preview{border-left:4px solid var(--accent);background:#1a2232;padding:15px;border-radius:7px;white-space:pre-wrap;margin-top:12px}.section{display:none}.section.active{display:block}.small{font-size:12px}.actioncell{white-space:nowrap}.login{max-width:440px;margin:12vh auto;padding:30px;text-align:center}.login .btn{display:inline-block}
@media(max-width:850px){.layout{grid-template-columns:1fr}aside{display:flex;overflow:auto;gap:5px;padding:9px;border-right:0;border-bottom:1px solid var(--line)}.navlabel{display:none}.nav{white-space:nowrap;width:auto;margin:0}.main{padding:16px}.stats{grid-template-columns:repeat(2,1fr)}}@media(max-width:560px){header{padding:0 14px}.head{display:block}.guildbox{margin-top:15px}.grid,.grid3{grid-template-columns:1fr}.stats{grid-template-columns:1fr 1fr}.card{padding:14px}}
</style></head><body>
<header><div class="brand">SYSTEM<span>-BOT</span> <span style="color:#71809b">/ DASHBOARD</span></div><div class="topright"><span id="who">Private owner access</span><a href="/announcement/logout">Logout</a></div></header>
<div class="layout"><aside>
<div class="navlabel">OVERVIEW</div><button class="nav active" data-tab="dashboard">▦ Dashboard</button>
<div class="navlabel">SERVER MANAGEMENT</div><button class="nav" data-tab="moderation">♜ Moderation</button><button class="nav" data-tab="roles">◈ Roles</button><button class="nav" data-tab="channels">▤ Channels</button><button class="nav" data-tab="automod">⛨ AutoMod</button>
<div class="navlabel">LEGENDS SYSTEMS</div><button class="nav" data-tab="economy">◆ LEGENDS Economy</button><button class="nav" data-tab="giveaways">🎉 Giveaways</button><button class="nav" data-tab="tickets">▣ Tickets</button><button class="nav" data-tab="announcements">✦ Announcement Studio</button>
</aside><main class="main"><div class="head"><div><h1 id="pageTitle">Dashboard</h1><div class="muted" id="pageDesc">Live overview of your Discord server and System-BOT.</div></div><div class="guildbox"><label style="margin-top:0">Active server</label><select id="guild"><option>Loading servers...</option></select></div></div>
<section id="dashboard" class="section active"><div class="stats" id="stats"><div class="stat"><small>Members</small><b>—</b></div><div class="stat"><small>Channels</small><b>—</b></div><div class="stat"><small>Roles</small><b>—</b></div><div class="stat"><small>Bot status</small><b>Online</b></div></div><div class="card" style="margin-top:17px"><h2>Server overview</h2><div id="overview" class="muted">Loading server information...</div></div></section>
<section id="moderation" class="section"><div class="grid"><div class="card"><h2>Member moderation</h2><label>Member ID</label><input id="modUser" placeholder="Discord user ID"><label>Action</label><select id="modAction"><option value="warn">Warn</option><option value="timeout">Timeout</option><option value="untimeout">Remove timeout</option><option value="kick">Kick</option><option value="ban">Ban</option><option value="unban">Unban by user ID</option><option value="warn_remove">Remove latest warning</option></select><label>Reason</label><input id="modReason" maxlength="500" placeholder="Reason for this action"><label>Timeout duration (minutes)</label><input id="modMinutes" type="number" min="1" max="40320" value="60"><button class="btn danger" onclick="moderate()">Apply moderation</button><div class="status" id="modStatus"></div></div><div class="card"><h2>Warning history</h2><label>Member ID</label><input id="historyUser" placeholder="Discord user ID"><button class="btn secondary" onclick="loadWarnings()">Load warnings & history</button><div id="warnings" class="status"></div></div></div></section>
<section id="roles" class="section"><div class="card"><h2>Create role</h2><div class="grid"><div><label>Role name</label><input id="roleName" maxlength="100" placeholder="Role name"></div><div><label>Role color</label><div class="colorrow"><input type="color" id="roleColor" value="#5865F2"><input id="roleHex" value="#5865F2" maxlength="7"></div></div></div><button class="btn" onclick="createRole()">Create role</button><div id="roleStatus" class="status"></div></div><div class="card"><div class="row"><h2 style="flex:1">Server roles</h2><button class="btn secondary" onclick="loadRoles()">Refresh</button></div><div id="rolesList" class="tablewrap muted">Loading roles...</div></div></section>
<section id="channels" class="section"><div class="card"><h2>Create channel</h2><div class="grid"><div><label>Channel name</label><input id="channelName" maxlength="90" placeholder="new-channel"></div><div><label>Type</label><select id="channelType"><option value="text">Text channel</option><option value="voice">Voice channel</option><option value="category">Category</option></select></div></div><label>Category (optional)</label><select id="channelCategory"><option value="">No category</option></select><button class="btn" onclick="createChannel()">Create channel</button><div id="channelStatus" class="status"></div></div><div class="card"><div class="row"><h2 style="flex:1">Channels</h2><button class="btn secondary" onclick="loadChannelsList()">Refresh</button></div><div id="channelsList" class="tablewrap muted">Loading channels...</div></div></section>
<section id="automod" class="section"><div class="card"><h2>AutoMod protection settings</h2><div id="automodSettings" class="muted">Loading settings...</div><button class="btn" onclick="saveAutoMod()">Save settings</button><div id="automodStatus" class="status"></div></div><div class="notice">These controls update the existing AutoMod settings file used by the running AutoMod cog.</div></section>
<section id="economy" class="section"><div class="card"><h2>Seasonal economy</h2><div id="economyStatus" class="notice">Loading active economy...</div><div class="grid"><div><label>Member ID</label><input id="ecoUser" placeholder="Discord user ID"></div><div><label>Economy</label><select id="ecoKey"></select></div><div><label>Account</label><select id="ecoAccount"><option value="wallet">Wallet</option><option value="bank">Bank</option></select></div><div><label>Amount</label><input id="ecoAmount" type="number" min="0" placeholder="0"></div></div><label class="check"><input type="checkbox" id="ecoInfinity"> Set infinity for this economy</label><button class="btn" onclick="setEconomyBalance()">Update balance</button><div id="ecoResult" class="status"></div></div></section>
<section id="giveaways" class="section"><div class="card"><h2>Create giveaway</h2><div class="grid"><div><label>Prize</label><input id="givePrize" maxlength="200" placeholder="Prize name"></div><div><label>Duration (minutes)</label><input id="giveDuration" type="number" min="1" max="43200" value="1440"></div><div><label>Number of winners</label><input id="giveWinners" type="number" min="1" max="20" value="1"></div><div><label>Announcement channel</label><select id="giveChannel"></select></div></div><button class="btn" onclick="createGiveaway()">Create giveaway</button><div id="giveStatus" class="status"></div></div><div class="card"><div class="row"><h2 style="flex:1">Giveaways</h2><button class="btn secondary" onclick="loadGiveaways()">Refresh</button></div><div id="giveList" class="tablewrap muted">Loading...</div></div></section>
<section id="tickets" class="section"><div class="card"><div class="row"><h2 style="flex:1">Support tickets & applications</h2><button class="btn secondary" onclick="loadTickets()">Refresh</button></div><div id="ticketList" class="tablewrap muted">Loading tickets...</div></div><div class="card"><h2>Ticket reply</h2><label>Ticket number</label><input id="ticketNumber" placeholder="0001"><label>Reply to user</label><textarea id="ticketReply" maxlength="1800" placeholder="Write a support reply..."></textarea><button class="btn" onclick="replyTicket()">Send reply</button><button class="btn danger" onclick="closeTicket()">Close ticket</button><div id="ticketStatus" class="status"></div></div></section>
<section id="announcements" class="section"><div class="card"><h2>Announcement Studio</h2><div class="grid"><div><label>Destination channel</label><select id="announceChannel"></select></div><div><label>Message format</label><select id="announceType"><option value="text">Regular message</option><option value="embed">Embed</option><option value="v2">Components V2</option></select></div></div><label>Message content</label><textarea id="announceContent" maxlength="2000" placeholder="Write announcement..."></textarea><div id="announceEmbed" class="hidden"><div class="grid"><div><label>Embed title</label><input id="announceTitle" maxlength="256"></div><div><label>Footer</label><input id="announceFooter" maxlength="2048"></div></div><label>Description</label><textarea id="announceDescription" maxlength="4096"></textarea><label>Accent color</label><div class="colorrow"><input type="color" id="announceColor" value="#5865F2"><input id="announceHex" value="#5865F2" maxlength="7"></div><label>Image URL</label><input id="announceImage" placeholder="https://..."></div><div id="announceV2" class="hidden"><label>Components V2 JSON</label><textarea id="announceComponents" style="min-height:160px">[{"type":10,"content":"Welcome to LEGENDS!"},{"type":14,"divider":true},{"type":10,"content":"New announcement"}]</textarea><div class="muted small">Supported component types: Text Display (10) and Separator (14).</div></div><label class="check"><input type="checkbox" id="allowRolePings" checked> Allow role and user mentions in this message</label><label class="check"><input type="checkbox" id="allowEveryone"> Allow @everyone and @here (use carefully)</label><button class="btn secondary" onclick="previewAnnouncement()">Preview</button><div id="announcePreview" class="preview hidden"></div><button class="btn" onclick="sendAnnouncement()">Publish announcement</button><div id="announceStatus" class="status"></div></div></section>
<div class="status" id="globalStatus"></div></main></div>
<script>
let csrfToken='';const $=id=>document.getElementById(id);let currentGuild='';
async function api(url,options={}){if(!csrfToken){let x=await fetch('/announcement/api/session');let j=await x.json();if(!x.ok)throw Error(j.error||'Session expired');csrfToken=j.csrf_token;$('who').textContent=j.username||'Owner';}let r=await fetch(url,{...options,headers:{'Content-Type':'application/json','X-CSRF-Token':csrfToken,...(options.headers||{})}});let d=await r.json();if(!r.ok)throw Error(d.error||'Request failed');return d}
function msg(id,t){$(id).textContent=t}function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}function gid(){return $('guild').value}
const pageInfo={dashboard:['Dashboard','Live overview of your Discord server and System-BOT.'],moderation:['Moderation','Manage member moderation, warnings and history.'],roles:['Roles','Create and manage server roles.'],channels:['Channels','Create and manage server channels.'],automod:['AutoMod','Configure the existing AutoMod protection system.'],economy:['LEGENDS Economy','Manage seasonal economy balances.'],giveaways:['Giveaways','Create and manage Discord giveaways.'],tickets:['Tickets','Manage support tickets and staff applications.'],announcements:['Announcement Studio','Compose and publish messages, embeds and Components V2.']};
document.querySelectorAll('.nav').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('.nav').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.querySelectorAll('.section').forEach(x=>x.classList.remove('active'));$(b.dataset.tab).classList.add('active');$('pageTitle').textContent=pageInfo[b.dataset.tab][0];$('pageDesc').textContent=pageInfo[b.dataset.tab][1];refreshTab(b.dataset.tab)}));
async function loadGuilds(){try{let d=await api('/announcement/api/guilds');$('guild').innerHTML='';d.guilds.forEach(g=>{let o=document.createElement('option');o.value=g.id;o.textContent=g.name;$('guild').append(o)});if(d.guilds.length){currentGuild=gid();await refreshTab('dashboard');await loadCommonChannels()}else $('guild').innerHTML='<option>No servers available</option>'}catch(e){msg('globalStatus',e.message)}}
$('guild').addEventListener('change',()=>{currentGuild=gid();loadCommonChannels();refreshTab(document.querySelector('.nav.active').dataset.tab)});
async function refreshTab(t){try{if(t==='dashboard')await loadDashboard();if(t==='roles')await loadRoles();if(t==='channels')await loadChannelsList();if(t==='automod')await loadAutoMod();if(t==='economy')await loadEconomy();if(t==='giveaways')await loadGiveaways();if(t==='tickets')await loadTickets();}catch(e){msg('globalStatus',e.message)}}
async function loadCommonChannels(){if(!gid())return;let d=await api('/announcement/api/channels/'+gid());['giveChannel','announceChannel','channelCategory'].forEach(id=>{$(id).innerHTML=id==='channelCategory'?'<option value="">No category</option>':'';});d.channels.forEach(c=>{let o=document.createElement('option');o.value=c.id;o.textContent='#'+c.name;$('giveChannel').append(o);let a=o.cloneNode(true);$('announceChannel').append(a)});d.categories.forEach(c=>{let o=document.createElement('option');o.value=c.id;o.textContent=c.name;$('channelCategory').append(o)})}
async function loadDashboard(){let d=await api('/announcement/api/stats/'+gid());$('stats').innerHTML=[['Members',d.members],['Text channels',d.channels],['Roles',d.roles],['Bot status','Online']].map(x=>`<div class="stat"><small>${x[0]}</small><b>${esc(x[1])}</b></div>`).join('');$('overview').innerHTML=`<div class="grid"><div><b>${esc(d.name)}</b><p class="muted">Server ID: ${esc(d.id)}</p><p class="muted">Created: ${esc(d.created)}</p></div><div><p>Owner: ${esc(d.owner)}</p><p>Boost level: ${esc(d.boost)}</p><p>Verification: ${esc(d.verification)}</p></div></div>`}
async function moderate(){try{let d=await api('/announcement/api/moderation/'+gid(),{method:'POST',body:JSON.stringify({user_id:$('modUser').value,action:$('modAction').value,reason:$('modReason').value,minutes:$('modMinutes').value})});msg('modStatus','Success: '+d.message)}catch(e){msg('modStatus','Error: '+e.message)}}
async function loadWarnings(){try{let d=await api('/announcement/api/warnings/'+gid()+'/'+encodeURIComponent($('historyUser').value));$('warnings').innerHTML='<b>Warnings</b><br>'+d.warnings.map(w=>`• ${esc(w.reason)} — ${esc(w.moderator)} <span class="muted">${esc(w.date)}</span>`).join('<br>')+'<br><br><b>Moderation history</b><br>'+d.history.map(h=>`• ${esc(h.action)}: ${esc(h.reason)} — ${esc(h.moderator)} <span class="muted">${esc(h.date)}</span>`).join('<br>')||'No records.'}catch(e){msg('warnings',e.message)}}
$('roleColor').addEventListener('input',e=>$('roleHex').value=e.target.value.toUpperCase());$('roleHex').addEventListener('input',e=>{if(/^#[0-9a-f]{6}$/i.test(e.target.value))$('roleColor').value=e.target.value});
async function loadRoles(){let d=await api('/announcement/api/roles/'+gid());$('rolesList').innerHTML='<table><thead><tr><th>Role</th><th>Members</th><th>Color</th><th>Action</th></tr></thead><tbody>'+d.roles.map(r=>`<tr><td>${esc(r.name)} <span class="muted small">${esc(r.id)}</span></td><td>${r.members}</td><td>${esc(r.color)}</td><td class="actioncell"><button class="btn danger" onclick="deleteRole('${r.id}')">Delete</button></td></tr>`).join('')+'</tbody></table>'}
async function createRole(){try{await api('/announcement/api/roles/'+gid(),{method:'POST',body:JSON.stringify({name:$('roleName').value,color:$('roleHex').value})});msg('roleStatus','Role created.');await loadRoles()}catch(e){msg('roleStatus',e.message)}}async function deleteRole(id){if(!confirm('Delete this role?'))return;try{await api('/announcement/api/roles/'+gid()+'/'+id,{method:'DELETE'});await loadRoles()}catch(e){alert(e.message)}}
async function loadChannelsList(){let d=await api('/announcement/api/channels/'+gid());$('channelsList').innerHTML='<table><thead><tr><th>Channel</th><th>Type</th><th>Category</th><th>Action</th></tr></thead><tbody>'+d.all.map(c=>`<tr><td>${esc(c.name)} <span class="muted small">${esc(c.id)}</span></td><td>${esc(c.type)}</td><td>${esc(c.category||'—')}</td><td><button class="btn danger" onclick="deleteChannel('${c.id}')">Delete</button></td></tr>`).join('')+'</tbody></table>'}
async function createChannel(){try{await api('/announcement/api/channels/'+gid(),{method:'POST',body:JSON.stringify({name:$('channelName').value,type:$('channelType').value,category_id:$('channelCategory').value})});msg('channelStatus','Channel created.');await loadChannelsList();await loadCommonChannels()}catch(e){msg('channelStatus',e.message)}}async function deleteChannel(id){if(!confirm('Delete this channel?'))return;try{await api('/announcement/api/channels/'+gid()+'/'+id,{method:'DELETE'});await loadChannelsList();await loadCommonChannels()}catch(e){alert(e.message)}}
async function loadAutoMod(){let d=await api('/announcement/api/automod/'+gid());$('automodSettings').innerHTML=Object.entries(d.settings).map(([k,v])=>`<label class="check"><input type="checkbox" data-setting="${esc(k)}" ${v?'checked':''}> ${esc(d.labels[k]||k)}</label>`).join('')}
async function saveAutoMod(){try{let settings={};document.querySelectorAll('[data-setting]').forEach(x=>settings[x.dataset.setting]=x.checked);await api('/announcement/api/automod/'+gid(),{method:'POST',body:JSON.stringify({settings})});msg('automodStatus','AutoMod settings saved.')}catch(e){msg('automodStatus',e.message)}}
async function loadEconomy(){let d=await api('/announcement/api/economy/'+gid());msg('economyStatus','Active economy: '+(d.active_name||'OFF'));$('ecoKey').innerHTML=d.economies.map(x=>`<option value="${esc(x.key)}">${esc(x.name)}</option>`).join('')}
async function setEconomyBalance(){try{let d=await api('/announcement/api/economy/'+gid(),{method:'POST',body:JSON.stringify({user_id:$('ecoUser').value,economy:$('ecoKey').value,account:$('ecoAccount').value,amount:$('ecoAmount').value,infinity:$('ecoInfinity').checked})});msg('ecoResult',d.message)}catch(e){msg('ecoResult',e.message)}}
async function createGiveaway(){try{let d=await api('/announcement/api/giveaways/'+gid(),{method:'POST',body:JSON.stringify({channel_id:$('giveChannel').value,prize:$('givePrize').value,duration:$('giveDuration').value,winners:$('giveWinners').value})});msg('giveStatus','Giveaway created: '+d.id);await loadGiveaways()}catch(e){msg('giveStatus',e.message)}}async function loadGiveaways(){let d=await api('/announcement/api/giveaways/'+gid());$('giveList').innerHTML=d.giveaways.length?'<table><thead><tr><th>Prize</th><th>Ends</th><th>Status</th><th>Action</th></tr></thead><tbody>'+d.giveaways.map(g=>`<tr><td>${esc(g.prize)}</td><td>${esc(g.ends)}</td><td><span class="pill ${g.ended?'bad':'good'}">${g.ended?'Ended':'Active'}</span></td><td>${g.ended?'—':`<button class="btn" onclick="endGiveaway('${g.id}')">End now</button>`}</td></tr>`).join('')+'</tbody></table>':'No giveaways yet.'}async function endGiveaway(id){try{await api('/announcement/api/giveaways/'+gid()+'/'+id,{method:'POST',body:'{}'});await loadGiveaways()}catch(e){alert(e.message)}}
async function loadTickets(){let d=await api('/announcement/api/tickets/'+gid());$('ticketList').innerHTML='<table><thead><tr><th>Number / User</th><th>Type</th><th>Details</th><th>Status / Actions</th></tr></thead><tbody>'+d.items.map(t=>`<tr><td>#${esc(t.number)}<br><span class="muted">${esc(t.user_id)}</span></td><td>${esc(t.type)}</td><td>${esc(t.details||'—')}<br><span class="muted small">Channel: ${esc(t.channel_id)}</span></td><td><span class="pill ${t.closed?'bad':'good'}">${t.closed?'Closed':'Open'}</span>${!t.closed&&t.type!=='Support'?`<br><button class="btn success" onclick="decideApplication('${esc(t.user_id)}','accept')">Accept</button><button class="btn danger" onclick="decideApplication('${esc(t.user_id)}','reject')">Reject</button>`:''}</td></tr>`).join('')+'</tbody></table>'}
async function decideApplication(uid,decision){if(!confirm((decision==='accept'?'Accept':'Reject')+' this application?'))return;try{await api('/announcement/api/tickets/'+gid()+'/application/'+uid+'/'+decision,{method:'POST',body:'{}'});await loadTickets()}catch(e){alert(e.message)}}
async function replyTicket(){try{let d=await api('/announcement/api/tickets/'+gid()+'/reply',{method:'POST',body:JSON.stringify({number:$('ticketNumber').value,message:$('ticketReply').value})});msg('ticketStatus',d.message)}catch(e){msg('ticketStatus',e.message)}}async function closeTicket(){try{let d=await api('/announcement/api/tickets/'+gid()+'/close',{method:'POST',body:JSON.stringify({number:$('ticketNumber').value})});msg('ticketStatus',d.message);await loadTickets()}catch(e){msg('ticketStatus',e.message)}}
$('announceType').addEventListener('change',()=>{$('announceEmbed').classList.toggle('hidden',$('announceType').value!=='embed');$('announceV2').classList.toggle('hidden',$('announceType').value!=='v2')});$('announceColor').addEventListener('input',e=>$('announceHex').value=e.target.value.toUpperCase());$('announceHex').addEventListener('input',e=>{if(/^#[0-9a-f]{6}$/i.test(e.target.value))$('announceColor').value=e.target.value});
function previewAnnouncement(){let text=$('announceContent').value;if($('announceType').value==='embed')text=$('announceTitle').value+'\n\n'+$('announceDescription').value+'\n\n'+text;if($('announceType').value==='v2')text=$('announceComponents').value;$('announcePreview').textContent=text;$('announcePreview').style.borderLeftColor=$('announceHex').value;$('announcePreview').classList.remove('hidden')}
async function sendAnnouncement(){try{let d=await api('/announcement/api/send',{method:'POST',body:JSON.stringify({guild_id:gid(),channel_id:$('announceChannel').value,type:$('announceType').value,content:$('announceContent').value,title:$('announceTitle').value,description:$('announceDescription').value,color:$('announceHex').value,footer:$('announceFooter').value,image:$('announceImage').value,components:$('announceComponents').value,allow_role_pings:$('allowRolePings').checked,allow_everyone:$('allowEveryone').checked})});msg('announceStatus','Announcement published successfully.')}catch(e){msg('announceStatus','Error: '+e.message)}}
loadGuilds();
</script></main></div></body></html>
"""


# =========================================================
# DISCORD API
# =========================================================

def discord_api_request(url, method="GET", data=None, token=None):
    headers = {
        "User-Agent": "System-BOT Announcement Studio",
        "Accept": "application/json",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = None

    if data is not None:
        body = urllib.parse.urlencode(data).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    req = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        logger.error(
            "Discord API error: HTTP %s: %s",
            error.code,
            error_body[:1000],
        )
        raise


def is_owner():
    return str(session.get("discord_user_id", "")) == str(OWNER_ID)


def csrf_valid():
    supplied = request.headers.get("X-CSRF-Token", "")
    expected = session.get("csrf_token", "")

    return bool(expected) and secrets.compare_digest(supplied, expected)


def get_guild(bot, guild_id):
    try:
        guild_id = int(guild_id)
    except (TypeError, ValueError):
        raise ValueError("Invalid server ID.")

    guild = bot.get_guild(guild_id)

    if guild is None:
        raise ValueError("The bot is not in this server.")

    return guild


# =========================================================
# COMPONENTS V2
# =========================================================

def build_components_v2(component_data, content=""):
    if not isinstance(component_data, list):
        raise ValueError("Components V2 must be a JSON array.")

    if len(component_data) > 25:
        raise ValueError("Maximum 25 components are allowed.")

    view = discord.ui.LayoutView(timeout=None)

    if content.strip():
        view.add_item(
            discord.ui.TextDisplay(content=content[:2000])
        )

    for item in component_data:
        if not isinstance(item, dict):
            raise ValueError("Each component must be an object.")

        component_type = item.get("type")

        if component_type == 10:
            text = item.get("content", "")

            if not isinstance(text, str) or not text.strip():
                raise ValueError("Text Display content cannot be empty.")

            view.add_item(
                discord.ui.TextDisplay(content=text[:4000])
            )

        elif component_type == 14:
            view.add_item(
                discord.ui.Separator(
                    visible=bool(item.get("divider", True)),
                    spacing=discord.SeparatorSpacing.small,
                )
            )

        else:
            raise ValueError(
                f"Unsupported component type: {component_type}"
            )

    if not view.children:
        raise ValueError("Add at least one Components V2 element.")

    return view


# =========================================================
# EXTENSION
# =========================================================

async def setup(bot):

    web_app = bot.web_app

    if not web_app.secret_key:
        web_app.secret_key = os.getenv("FLASK_SECRET_KEY")

    if not web_app.secret_key:
        raise RuntimeError(
            "FLASK_SECRET_KEY is missing from Railway Variables."
        )

    web_app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_NAME="system_bot_session",
    )

    if not CLIENT_ID or not CLIENT_SECRET:
        logger.warning("Announcement Studio OAuth2 variables are missing.")

    # LOGIN

    @web_app.route("/announcement/login")
    def announcement_login():

        if not CLIENT_ID or not CLIENT_SECRET:
            return "Discord OAuth2 is not configured.", 503

        state = secrets.token_urlsafe(32)
        session["oauth_state"] = state

        params = {
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": "identify",
            "state": state,
        }

        return redirect(
            "https://discord.com/oauth2/authorize?"
            + urllib.parse.urlencode(params)
        )

    # OAUTH CALLBACK

    @web_app.route("/announcement/callback")
    def announcement_callback():

        if request.args.get("error"):
            return "Discord authorization was cancelled.", 400

        code = request.args.get("code")
        state = request.args.get("state")

        saved_state = session.pop("oauth_state", None)

        if (
            not code
            or not saved_state
            or not secrets.compare_digest(saved_state, state or "")
        ):
            return "Invalid OAuth2 state.", 400

        try:
            token_data = discord_api_request(
                f"{DISCORD_API}/oauth2/token",
                method="POST",
                data={
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": REDIRECT_URI,
                },
            )

            access_token = token_data["access_token"]

            user = discord_api_request(
                f"{DISCORD_API}/users/@me",
                token=access_token,
            )

            if str(user.get("id")) != str(OWNER_ID):
                session.clear()
                return "Access denied. This website is private.", 403

            session.clear()
            session["discord_user_id"] = str(user["id"])
            session["discord_username"] = user.get("username", "Owner")
            session["csrf_token"] = secrets.token_urlsafe(32)

            return redirect("/announcement")

        except urllib.error.HTTPError:
            logger.exception("Discord OAuth2 HTTP error")
            return "Discord OAuth2 failed. Check Railway logs.", 400

        except Exception:
            logger.exception("Discord OAuth2 callback failed")
            return "Discord authentication failed. Check Railway logs.", 500

    # LOGOUT

    @web_app.route("/announcement/logout")
    def announcement_logout():
        session.clear()
        return redirect("/announcement/login")

    # DASHBOARD

    @web_app.route("/announcement")
    def announcement_page():

        if not is_owner():
            return redirect("/announcement/login")

        response = web_app.make_response(
            render_template_string(HTML)
        )

        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"

        return response

    # SESSION

    @web_app.route("/announcement/api/session")
    def announcement_session():

        if not is_owner():
            return jsonify(error="Unauthorized"), 401

        return jsonify(
            csrf_token=session.get("csrf_token"),
            username=session.get("discord_username"),
        )

    # GUILDS

    @web_app.route("/announcement/api/guilds")
    def announcement_guilds():

        if not is_owner():
            return jsonify(error="Unauthorized"), 401

        return jsonify(
            guilds=[
                {"id": str(g.id), "name": g.name}
                for g in bot.guilds
            ]
        )

    # CHANNELS

    @web_app.route("/announcement/api/channels/<guild_id>")
    def announcement_channels(guild_id):

        if not is_owner():
            return jsonify(error="Unauthorized"), 401

        try:
            guild = get_guild(bot, guild_id)
            channels = []

            for channel in guild.text_channels:
                permissions = channel.permissions_for(guild.me)

                if permissions.send_messages:
                    channels.append({
                        "id": str(channel.id),
                        "name": channel.name,
                    })

            all_channels = [
                {"id": str(c.id), "name": c.name,
                 "type": str(c.type).replace("_", " "),
                 "category": c.category.name if getattr(c, "category", None) else None}
                for c in guild.channels
            ]
            categories = [{"id": str(c.id), "name": c.name} for c in guild.categories]
            return jsonify(
                channels=channels,
                all=all_channels,
                categories=categories,
            )

        except ValueError as error:
            return jsonify(error=str(error)), 400

        except Exception:
            logger.exception("Channel loading failed")
            return jsonify(error="Failed to load channels."), 500

    # ---------------------------------------------------------
    # DASHBOARD API HELPERS + MANAGEMENT ROUTES
    # ---------------------------------------------------------
    import importlib
    import os as _os

    def require_owner_json():
        if not is_owner():
            return jsonify(error="Unauthorized"), 401
        return None

    def require_csrf_json():
        if not csrf_valid():
            return jsonify(error="Invalid CSRF token."), 403
        return None

    def run_on_bot(coro, timeout=30):
        if not bot.loop or not bot.loop.is_running():
            raise RuntimeError("Discord bot is not ready.")
        future = asyncio.run_coroutine_threadsafe(coro, bot.loop)
        return future.result(timeout=timeout)

    def get_cog_module(attribute):
        for module in list(sys.modules.values()):
            if module and getattr(module, attribute, None) is not None:
                return module
        return None

    def get_ticket_cog():
        cog = bot.get_cog("TicketCog")
        if cog is None:
            raise RuntimeError("Ticket system is not loaded.")
        return cog

    def get_automod_module():
        module = get_cog_module("get_settings")
        if module is None or not hasattr(module, "save_settings"):
            raise RuntimeError("AutoMod system is not loaded.")
        return module

    def get_economy_module():
        module = get_cog_module("active_economy")
        if module is None or not hasattr(module, "ECONOMIES"):
            raise RuntimeError("LEGENDS Economy is not loaded.")
        return module

    def get_member_sync(guild, user_id):
        try:
            uid = int(user_id)
        except (TypeError, ValueError):
            raise ValueError("Invalid member ID.")
        member = guild.get_member(uid)
        if member is None:
            raise ValueError("Member is not in this server or is not cached.")
        return member

    @web_app.route("/announcement/api/stats/<guild_id>")
    def dashboard_stats(guild_id):
        if not is_owner(): return jsonify(error="Unauthorized"), 401
        try:
            g = get_guild(bot, guild_id)
            owner = g.owner or g.get_member(g.owner_id)
            return jsonify(id=str(g.id), name=g.name, members=g.member_count or len(g.members),
                channels=len(g.channels), roles=len(g.roles), owner=str(owner or g.owner_id),
                created=g.created_at.strftime("%Y-%m-%d"), boost=g.premium_tier,
                verification=str(g.verification_level).replace("_", " ").title())
        except Exception as e: return jsonify(error=str(e)), 400

    @web_app.route("/announcement/api/roles/<guild_id>", methods=["GET", "POST"])
    def dashboard_roles(guild_id):
        if not is_owner(): return jsonify(error="Unauthorized"), 401
        try:
            g=get_guild(bot,guild_id)
            if request.method == "GET":
                return jsonify(roles=[{"id":str(r.id),"name":r.name,"members":len(r.members),"color":str(r.color)} for r in sorted(g.roles,key=lambda x:x.position,reverse=True)])
            if not csrf_valid(): return jsonify(error="Invalid CSRF token."),403
            d=request.get_json(silent=True) or {}; name=str(d.get("name","")).strip()[:100]; color=str(d.get("color","#5865F2"))
            if not name: return jsonify(error="Role name is required."),400
            if not (len(color)==7 and color.startswith("#") and all(c in "0123456789abcdefABCDEF" for c in color[1:])): return jsonify(error="Invalid HEX color."),400
            async def create():
                me=g.me
                if not me.guild_permissions.manage_roles: raise PermissionError("Bot needs Manage Roles permission.")
                return await g.create_role(name=name,color=discord.Color(int(color[1:],16)),reason="Created from System-BOT Dashboard")
            role=run_on_bot(create())
            return jsonify(success=True,id=str(role.id))
        except PermissionError as e:return jsonify(error=str(e)),403
        except Exception as e:return jsonify(error=str(e)),400

    @web_app.route("/announcement/api/roles/<guild_id>/<role_id>", methods=["DELETE"])
    def dashboard_role_delete(guild_id,role_id):
        if not is_owner(): return jsonify(error="Unauthorized"),401
        if not csrf_valid(): return jsonify(error="Invalid CSRF token."),403
        try:
            g=get_guild(bot,guild_id); role=g.get_role(int(role_id))
            if not role:return jsonify(error="Role not found."),404
            if role.is_default() or role.managed:return jsonify(error="This role cannot be deleted."),400
            async def delete():
                if not g.me.guild_permissions.manage_roles:raise PermissionError("Bot needs Manage Roles permission.")
                if g.me.top_role <= role:raise PermissionError("Move the bot role above this role.")
                await role.delete(reason="Deleted from System-BOT Dashboard")
            run_on_bot(delete());return jsonify(success=True)
        except PermissionError as e:return jsonify(error=str(e)),403
        except Exception as e:return jsonify(error=str(e)),400

    @web_app.route("/announcement/api/channels/<guild_id>", methods=["GET","POST"])
    def dashboard_channels(guild_id):
        if not is_owner():return jsonify(error="Unauthorized"),401
        try:
            g=get_guild(bot,guild_id)
            if request.method=="GET":
                sendable=[]
                for c in g.text_channels:
                    if c.permissions_for(g.me).send_messages:sendable.append({"id":str(c.id),"name":c.name})
                all_channels=[{"id":str(c.id),"name":c.name,"type":str(c.type).replace("_"," "),"category":c.category.name if getattr(c,"category",None) else None} for c in g.channels]
                cats=[{"id":str(c.id),"name":c.name} for c in g.categories]
                return jsonify(channels=sendable,all=all_channels,categories=cats)
            if not csrf_valid():return jsonify(error="Invalid CSRF token."),403
            d=request.get_json(silent=True) or {};name=str(d.get("name","")).strip().lower().replace(" ","-")[:90];typ=d.get("type");cat_id=d.get("category_id")
            if not name:return jsonify(error="Channel name is required."),400
            if typ not in ("text","voice","category"):return jsonify(error="Invalid channel type."),400
            cat=g.get_channel(int(cat_id)) if cat_id else None
            async def create():
                if not g.me.guild_permissions.manage_channels:raise PermissionError("Bot needs Manage Channels permission.")
                if typ=="text":return await g.create_text_channel(name,category=cat if isinstance(cat,discord.CategoryChannel) else None)
                if typ=="voice":return await g.create_voice_channel(name,category=cat if isinstance(cat,discord.CategoryChannel) else None)
                return await g.create_category(name)
            c=run_on_bot(create());return jsonify(success=True,id=str(c.id))
        except PermissionError as e:return jsonify(error=str(e)),403
        except Exception as e:return jsonify(error=str(e)),400

    @web_app.route("/announcement/api/channels/<guild_id>/<channel_id>",methods=["DELETE"])
    def dashboard_channel_delete(guild_id,channel_id):
        if not is_owner():return jsonify(error="Unauthorized"),401
        if not csrf_valid():return jsonify(error="Invalid CSRF token."),403
        try:
            g=get_guild(bot,guild_id);c=g.get_channel(int(channel_id))
            if c is None:return jsonify(error="Channel not found."),404
            async def delete():
                if not g.me.guild_permissions.manage_channels:raise PermissionError("Bot needs Manage Channels permission.")
                await c.delete(reason="Deleted from System-BOT Dashboard")
            run_on_bot(delete());return jsonify(success=True)
        except PermissionError as e:return jsonify(error=str(e)),403
        except Exception as e:return jsonify(error=str(e)),400

    @web_app.route("/announcement/api/moderation/<guild_id>",methods=["POST"])
    def dashboard_moderation(guild_id):
        if not is_owner():return jsonify(error="Unauthorized"),401
        if not csrf_valid():return jsonify(error="Invalid CSRF token."),403
        try:
            g=get_guild(bot,guild_id);d=request.get_json(silent=True) or {};action=d.get("action");reason=str(d.get("reason","No reason provided"))[:500];uid=int(d.get("user_id"))
            automod=get_automod_module()
            async def apply():
                if action=="unban":
                    if not g.me.guild_permissions.ban_members:raise PermissionError("Bot needs Ban Members permission.")
                    await g.unban(discord.Object(id=uid),reason=reason);return "User unbanned."
                member=await g.fetch_member(uid)
                if action=="warn":
                    automod.add_warning(g.id,member.id,reason,"Dashboard Owner")
                    automod.add_history(g,member,"Dashboard Owner","Warn",reason)
                    await automod.send_log(g,member,"Dashboard Owner","Warn",reason,source="Dashboard")
                    return "Warning added."
                if action=="warn_remove":
                    removed=automod.remove_warning(g.id,member.id)
                    if removed is None:raise ValueError("This member has no warnings.")
                    automod.add_history(g,member,"Dashboard Owner","Warning Removed",reason)
                    return "Latest warning removed."
                if action=="timeout":
                    if not g.me.guild_permissions.moderate_members:raise PermissionError("Bot needs Moderate Members permission.")
                    mins=max(1,min(40320,int(d.get("minutes",60))))
                    await member.timeout(timedelta(minutes=mins),reason=reason)
                    automod.add_history(g,member,"Dashboard Owner","Timeout",reason,extra={"minutes":mins})
                    await automod.send_log(g,member,"Dashboard Owner","Timeout",reason,source="Dashboard",extra={"Duration":f"{mins} minutes"})
                    return f"Member timed out for {mins} minutes."
                if action=="untimeout":
                    await member.timeout(None,reason=reason);automod.add_history(g,member,"Dashboard Owner","Timeout Removed",reason);return "Timeout removed."
                if action=="kick":
                    await member.kick(reason=reason);automod.add_history(g,member,"Dashboard Owner","Kick",reason);await automod.send_log(g,member,"Dashboard Owner","Kick",reason,source="Dashboard");return "Member kicked."
                if action=="ban":
                    await member.ban(reason=reason,delete_message_seconds=0);automod.add_history(g,member,"Dashboard Owner","Ban",reason);await automod.send_log(g,member,"Dashboard Owner","Ban",reason,source="Dashboard");return "Member banned."
                raise ValueError("Unsupported moderation action.")
            result=run_on_bot(apply());return jsonify(success=True,message=result)
        except PermissionError as e:return jsonify(error=str(e)),403
        except discord.NotFound:return jsonify(error="Member or ban entry not found."),404
        except Exception as e:return jsonify(error=str(e)),400

    @web_app.route("/announcement/api/warnings/<guild_id>/<user_id>")
    def dashboard_warnings(guild_id,user_id):
        if not is_owner():return jsonify(error="Unauthorized"),401
        try:
            g=get_guild(bot,guild_id);uid=int(user_id);m=get_automod_module();warnings=m.get_warnings(g.id,uid);history=m.history_data.get(str(g.id),[])
            return jsonify(warnings=[{"reason":x.get("reason"),"moderator":x.get("moderator"),"date":datetime.fromtimestamp(x.get("timestamp",0),timezone.utc).strftime("%Y-%m-%d %H:%M UTC")} for x in warnings],history=[{"action":x.get("action"),"reason":x.get("reason"),"moderator":x.get("moderator"),"date":datetime.fromtimestamp(x.get("timestamp",0),timezone.utc).strftime("%Y-%m-%d %H:%M UTC")} for x in history if int(x.get("member_id",0))==uid][-30:])
        except Exception as e:return jsonify(error=str(e)),400

    @web_app.route("/announcement/api/automod/<guild_id>",methods=["GET","POST"])
    def dashboard_automod(guild_id):
        if not is_owner():return jsonify(error="Unauthorized"),401
        try:
            g=get_guild(bot,guild_id);m=get_automod_module();settings=m.get_settings(g.id)
            labels={"enabled":"AutoMod Enabled","bad_words":"Bad Words Filter","links":"Link Filter","spam":"Anti-Spam","duplicates":"Duplicate Messages","bypass_protection":"Bypass Protection"}
            if request.method=="GET":return jsonify(settings=settings,labels=labels)
            if not csrf_valid():return jsonify(error="Invalid CSRF token."),403
            d=request.get_json(silent=True) or {};new=d.get("settings")
            if not isinstance(new,dict):return jsonify(error="Invalid settings."),400
            for key in labels:
                if key in new:settings[key]=bool(new[key])
            m.save_settings();return jsonify(success=True)
        except Exception as e:return jsonify(error=str(e)),400

    @web_app.route("/announcement/api/economy/<guild_id>",methods=["GET","POST"])
    def dashboard_economy(guild_id):
        if not is_owner():return jsonify(error="Unauthorized"),401
        try:
            g=get_guild(bot,guild_id);m=get_economy_module();active=m.active_economy()
            if request.method=="GET":return jsonify(active=active,active_name=m.ECONOMIES.get(active,{}).get("name") if active in m.ECONOMIES else "OFF",economies=[{"key":k,"name":v["name"]} for k,v in m.ECONOMIES.items()])
            if not csrf_valid():return jsonify(error="Invalid CSRF token."),403
            d=request.get_json(silent=True) or {};uid=int(d.get("user_id"));key=str(d.get("economy",""));account=d.get("account");amount=max(0,int(d.get("amount",0)));infinity=bool(d.get("infinity"))
            if key not in m.ECONOMIES:return jsonify(error="Unknown economy."),400
            async def update():
                member=await g.fetch_member(uid)
                m.ensure_balance(g.id,member.id,key)
                with m.db() as con:
                    if infinity:con.execute("UPDATE balances SET infinity=1 WHERE guild_id=? AND user_id=? AND economy=?",(g.id,uid,key))
                    else:
                        if account not in ("wallet","bank"):raise ValueError("Choose Wallet or Bank.")
                        con.execute(f"UPDATE balances SET {account}=?,infinity=0 WHERE guild_id=? AND user_id=? AND economy=?",(amount,g.id,uid,key))
                return member
            member=run_on_bot(update());return jsonify(success=True,message=(f"Granted infinity balance to {member.display_name}." if infinity else f"Updated {account} for {member.display_name} to {amount:,}."))
        except Exception as e:return jsonify(error=str(e)),400

    # Giveaways use a dedicated JSON file; existing bot data files remain untouched.
    GIVEAWAY_DIR=_os.getenv("DATA_DIR",".")
    _os.makedirs(GIVEAWAY_DIR, exist_ok=True)
    GIVEAWAY_FILE=_os.path.join(GIVEAWAY_DIR,"dashboard_giveaways.json")
    def read_giveaways():
        try:
            with open(GIVEAWAY_FILE,"r",encoding="utf-8") as f:return json.load(f)
        except Exception:return {}
    def write_giveaways(data):
        tmp=GIVEAWAY_FILE+".tmp"
        with open(tmp,"w",encoding="utf-8") as f:json.dump(data,f,ensure_ascii=False,indent=2)
        _os.replace(tmp,GIVEAWAY_FILE)

    @web_app.route("/announcement/api/giveaways/<guild_id>",methods=["GET","POST"])
    def dashboard_giveaways(guild_id):
        if not is_owner():return jsonify(error="Unauthorized"),401
        try:
            g=get_guild(bot,guild_id);all_data=read_giveaways();items=all_data.get(str(g.id),[])
            if request.method=="GET":return jsonify(giveaways=[{"id":x["id"],"prize":x["prize"],"ends":datetime.fromtimestamp(x["ends"],timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),"ended":x.get("ended",False)} for x in items])
            if not csrf_valid():return jsonify(error="Invalid CSRF token."),403
            d=request.get_json(silent=True) or {};channel=g.get_channel(int(d.get("channel_id",0)));prize=str(d.get("prize","")).strip()[:200];duration=max(1,min(43200,int(d.get("duration",1440))));winners=max(1,min(20,int(d.get("winners",1))))
            if not isinstance(channel,discord.TextChannel):return jsonify(error="Choose a valid text channel."),400
            if not prize:return jsonify(error="Prize is required."),400
            gid=str(secrets.token_hex(5));ends=int(time.time())+duration*60
            async def create():
                if not channel.permissions_for(g.me).send_messages or not channel.permissions_for(g.me).add_reactions:raise PermissionError("Bot needs Send Messages and Add Reactions permissions.")
                message=await channel.send(f"🎉 **GIVEAWAY** 🎉\n\nPrize: **{discord.utils.escape_markdown(prize)}**\nWinners: **{winners}**\nEnds: <t:{ends}:R>\n\nReact with 🎉 to enter!")
                await message.add_reaction("🎉");return message
            message=run_on_bot(create());items.append({"id":gid,"prize":prize,"channel_id":channel.id,"message_id":message.id,"ends":ends,"winners":winners,"ended":False});all_data[str(g.id)]=items;write_giveaways(all_data)
            return jsonify(success=True,id=gid)
        except PermissionError as e:return jsonify(error=str(e)),403
        except Exception as e:return jsonify(error=str(e)),400

    @web_app.route("/announcement/api/giveaways/<guild_id>/<giveaway_id>",methods=["POST"])
    def dashboard_giveaway_end(guild_id,giveaway_id):
        if not is_owner():return jsonify(error="Unauthorized"),401
        if not csrf_valid():return jsonify(error="Invalid CSRF token."),403
        try:
            g=get_guild(bot,guild_id);data=read_giveaways();items=data.get(str(g.id),[]);entry=next((x for x in items if x["id"]==giveaway_id),None)
            if not entry:return jsonify(error="Giveaway not found."),404
            if entry.get("ended"):return jsonify(error="Giveaway already ended."),400
            async def finish():
                channel=g.get_channel(int(entry["channel_id"]))
                if not isinstance(channel,discord.TextChannel):raise ValueError("Giveaway channel no longer exists.")
                message=await channel.fetch_message(int(entry["message_id"]))
                reaction=next((r for r in message.reactions if str(r.emoji)=="🎉"),None)
                entrants=[]
                if reaction:
                    async for user in reaction.users():
                        if not user.bot:entrants.append(user)
                random.shuffle(entrants);selected=entrants[:int(entry["winners"])]
                entry["ended"]=True
                if selected:
                    mentions=", ".join(u.mention for u in selected)
                    await channel.send(f"🎉 Giveaway ended! Prize: **{discord.utils.escape_markdown(entry['prize'])}**\nWinner(s): {mentions}",allowed_mentions=discord.AllowedMentions(users=True,roles=False,everyone=False))
                else:await channel.send(f"Giveaway ended for **{discord.utils.escape_markdown(entry['prize'])}**, but there were no valid entries.")
            run_on_bot(finish());write_giveaways(data);return jsonify(success=True)
        except Exception as e:return jsonify(error=str(e)),400

    @web_app.route("/announcement/api/tickets/<guild_id>")
    def dashboard_tickets(guild_id):
        if not is_owner():return jsonify(error="Unauthorized"),401
        try:
            g=get_guild(bot,guild_id);c=get_ticket_cog();items=[]
            for number,t in c.data.get("tickets",{}).items():
                items.append({"number":number,"user_id":str(t.get("user_id")),"channel_id":str(t.get("channel_id")),"type":"Support","closed":bool(t.get("closed")),"details":f"{t.get('language','')} • {t.get('issue','')}"})
            for uid,a in c.data.get("applications",{}).items():
                items.append({"number":str(a.get("ticket_number", "APP")),"user_id":str(uid),"channel_id":str(a.get("channel_id")),"type":f"{a.get('type','Application').title()} application","closed":bool(a.get("closed",False)),"details":"Application review"})
            return jsonify(items=items)
        except Exception as e:return jsonify(error=str(e)),400

    @web_app.route("/announcement/api/tickets/<guild_id>/application/<user_id>/<decision>",methods=["POST"])
    def dashboard_application_decision(guild_id,user_id,decision):
        if not is_owner():return jsonify(error="Unauthorized"),401
        if not csrf_valid():return jsonify(error="Invalid CSRF token."),403
        if decision not in ("accept","reject"):return jsonify(error="Invalid decision."),400
        try:
            g=get_guild(bot,guild_id);c=get_ticket_cog();key=str(int(user_id));application=c.data.get("applications",{}).get(key)
            if not application:return jsonify(error="Application not found."),404
            accepted=decision=="accept";app_type=application.get("type","staff")
            role_id=1542739534343700500 if app_type=="staff" else 1539734753736134856
            role_name="Staff┃| Host" if app_type=="staff" else "Moderator"
            async def decide():
                member=None
                try:member=await g.fetch_member(int(key))
                except discord.NotFound:pass
                user=await bot.fetch_user(int(key))
                channel=bot.get_channel(int(application.get("channel_id",0)))
                if accepted:
                    if member is None:raise ValueError("Applicant is no longer in this server.")
                    role=g.get_role(role_id)
                    if role is None:raise ValueError(f"The {role_name} role was not found.")
                    if not g.me.guild_permissions.manage_roles:raise PermissionError("Bot needs Manage Roles permission.")
                    if g.me.top_role<=role:raise PermissionError("Move the bot role above the application role.")
                    if role not in member.roles:await member.add_roles(role,reason=f"{app_type} application accepted from Dashboard")
                    result=f"✅ Your {role_name} application has been accepted! You have received the {role_name} role."
                else:
                    result=f"Your {role_name} application has been rejected. Thank you for applying."
                try:await user.send(result)
                except (discord.Forbidden,discord.HTTPException):pass
                del c.data["applications"][key]
                module=get_cog_module("DEFAULT_DATA")
                if module and hasattr(module,"save_data"):module.save_data(c.data)
                if channel:await channel.delete(reason=f"Application {decision} from Dashboard")
            run_on_bot(decide());return jsonify(success=True,message=f"Application {decision}ed.")
        except PermissionError as e:return jsonify(error=str(e)),403
        except Exception as e:return jsonify(error=str(e)),400

    @web_app.route("/announcement/api/tickets/<guild_id>/reply",methods=["POST"])
    def dashboard_ticket_reply(guild_id):
        if not is_owner():return jsonify(error="Unauthorized"),401
        if not csrf_valid():return jsonify(error="Invalid CSRF token."),403
        try:
            g=get_guild(bot,guild_id);d=request.get_json(silent=True) or {};number=str(d.get("number","")).strip();message=str(d.get("message","")).strip();c=get_ticket_cog();ticket=c.data.get("tickets",{}).get(number)
            if not ticket:return jsonify(error="Support ticket not found."),404
            if ticket.get("closed"):return jsonify(error="This ticket is already closed."),400
            if not message:return jsonify(error="Reply cannot be empty."),400
            async def reply():
                user=await bot.fetch_user(int(ticket["user_id"]));await user.send(f"**Support:** {message[:1800]}")
                ch=bot.get_channel(int(ticket["channel_id"]))
                if ch:await ch.send(embed=discord.Embed(description=f"**Support:** {message[:1800]}",color=discord.Color.light_grey()))
            run_on_bot(reply());return jsonify(success=True,message="Reply sent to the user and ticket channel.")
        except discord.Forbidden:return jsonify(error="Could not DM the user. Their privacy settings may block messages."),400
        except Exception as e:return jsonify(error=str(e)),400

    @web_app.route("/announcement/api/tickets/<guild_id>/close",methods=["POST"])
    def dashboard_ticket_close(guild_id):
        if not is_owner():return jsonify(error="Unauthorized"),401
        if not csrf_valid():return jsonify(error="Invalid CSRF token."),403
        try:
            g=get_guild(bot,guild_id);d=request.get_json(silent=True) or {};number=str(d.get("number","")).strip();c=get_ticket_cog();ticket=c.data.get("tickets",{}).get(number)
            if not ticket:return jsonify(error="Support ticket not found."),404
            if ticket.get("closed"):return jsonify(error="Ticket already closed."),400
            async def close():
                try:
                    user=await bot.fetch_user(int(ticket["user_id"]));close_ch=bot.get_channel(1555925139546439700);link=close_ch.jump_url if close_ch else f"https://discord.com/channels/{g.id}/{1555925139546439700}"
                    await user.send("🔒 **Your ticket has been closed.**\n\nTo create a new ticket, please use the server ticket panel.")
                except Exception:pass
                ticket["closed"]=True
                # Persist using the original ticket module's save_data function.
                module=get_cog_module("DEFAULT_DATA")
                if module and hasattr(module,"save_data"):module.save_data(c.data)
                ch=bot.get_channel(int(ticket["channel_id"]))
                if ch:await ch.delete(reason=f"Ticket {number} closed from Dashboard")
            run_on_bot(close());return jsonify(success=True,message="Ticket closed.")
        except Exception as e:return jsonify(error=str(e)),400


    async def dashboard_giveaway_scheduler():
        await bot.wait_until_ready()
        while not bot.is_closed():
            await asyncio.sleep(30)
            try:
                data=read_giveaways();changed=False
                for guild_key, entries in data.items():
                    guild=bot.get_guild(int(guild_key))
                    if guild is None:continue
                    for entry in entries:
                        if entry.get("ended") or int(entry.get("ends",0))>int(time.time()):continue
                        channel=guild.get_channel(int(entry.get("channel_id",0)))
                        if not isinstance(channel,discord.TextChannel):
                            entry["ended"]=True;changed=True;continue
                        try:
                            message=await channel.fetch_message(int(entry["message_id"]))
                            reaction=next((r for r in message.reactions if str(r.emoji)=="🎉"),None)
                            entrants=[]
                            if reaction:
                                async for user in reaction.users():
                                    if not user.bot:entrants.append(user)
                            random.shuffle(entrants);selected=entrants[:int(entry.get("winners",1))]
                            if selected:
                                mentions=", ".join(user.mention for user in selected)
                                await channel.send(f"🎉 Giveaway ended! Prize: **{discord.utils.escape_markdown(entry['prize'])}**\\nWinner(s): {mentions}",allowed_mentions=discord.AllowedMentions(users=True,roles=False,everyone=False))
                            else:
                                await channel.send(f"Giveaway ended for **{discord.utils.escape_markdown(entry['prize'])}**, but there were no valid entries.")
                            entry["ended"]=True;changed=True
                        except (discord.NotFound,discord.Forbidden,discord.HTTPException):
                            logger.exception("Could not automatically end giveaway %s",entry.get("id"))
                if changed:write_giveaways(data)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Giveaway scheduler iteration failed")

    old_giveaway_task=getattr(bot,"_dashboard_giveaway_task",None)
    if old_giveaway_task and not old_giveaway_task.done():
        old_giveaway_task.cancel()
    bot._dashboard_giveaway_task=bot.loop.create_task(dashboard_giveaway_scheduler())

    # SEND ANNOUNCEMENT

    @web_app.route("/announcement/api/send", methods=["POST"])
    def announcement_send():

        if not is_owner():
            return jsonify(error="Unauthorized"), 401

        if not csrf_valid():
            return jsonify(error="Invalid CSRF token."), 403

        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify(error="Invalid request."), 400

        message_type = data.get("type")

        if message_type not in ("text", "embed", "v2"):
            return jsonify(error="Invalid announcement type."), 400

        try:
            guild = get_guild(bot, data.get("guild_id"))

            try:
                channel_id = int(data.get("channel_id"))
            except (TypeError, ValueError):
                return jsonify(error="Invalid channel ID."), 400

            channel = guild.get_channel(channel_id)

            if not isinstance(channel, discord.TextChannel):
                return jsonify(error="Invalid text channel."), 400

            permissions = channel.permissions_for(guild.me)

            if not permissions.send_messages:
                return jsonify(error="Bot cannot send messages here."), 403

            content = str(data.get("content", ""))[:2000]
            allow_roles_users = bool(data.get("allow_role_pings", False))
            allow_everyone = bool(data.get("allow_everyone", False))
            mention_policy = discord.AllowedMentions(
                everyone=allow_everyone,
                users=allow_roles_users,
                roles=allow_roles_users,
            )

            async def send_message():

                if message_type == "text":

                    if not content.strip():
                        raise ValueError("Message cannot be empty.")

                    await channel.send(
                        content=content,
                        allowed_mentions=mention_policy,
                    )

                elif message_type == "embed":

                    title = str(data.get("title", ""))[:256]
                    description = str(data.get("description", ""))[:4096]
                    footer = str(data.get("footer", ""))[:2048]
                    image = str(data.get("image", ""))[:1000]
                    color_text = str(data.get("color", "#5865F2"))

                    if not content.strip() and not title and not description:
                        raise ValueError("Announcement cannot be empty.")

                    if not (
                        len(color_text) == 7
                        and color_text.startswith("#")
                        and all(
                            c in "0123456789abcdefABCDEF"
                            for c in color_text[1:]
                        )
                    ):
                        raise ValueError("Invalid HEX color.")

                    embed = discord.Embed(
                        title=title or None,
                        description=description or None,
                        color=int(color_text[1:], 16),
                    )

                    if footer:
                        embed.set_footer(text=footer)

                    if image:
                        if not image.startswith(("https://", "http://")):
                            raise ValueError("Invalid image URL.")

                        embed.set_image(url=image)

                    await channel.send(
                        content=content or None,
                        embed=embed,
                        allowed_mentions=mention_policy,
                    )

                elif message_type == "v2":

                    try:
                        components = json.loads(data.get("components", ""))
                    except (TypeError, json.JSONDecodeError):
                        raise ValueError("Invalid Components V2 JSON.")

                    view = build_components_v2(components, content)

                    await channel.send(
                        view=view,
                        allowed_mentions=mention_policy,
                    )

            future = asyncio.run_coroutine_threadsafe(
                send_message(),
                bot.loop,
            )

            future.result(timeout=30)

            return jsonify(success=True)

        except ValueError as error:
            return jsonify(error=str(error)), 400

        except discord.Forbidden:
            return jsonify(error="Bot has no permission to send messages."), 403

        except discord.HTTPException:
            logger.exception("Discord send error")
            return jsonify(error="Discord rejected the announcement."), 400

        except Exception:
            logger.exception("Announcement send failed")
            return jsonify(error="Failed to send announcement."), 500

    # REGISTER SLASH COMMAND

    send_group = bot.tree.get_command("send")

    if send_group is None or not isinstance(send_group, app_commands.Group):
        raise RuntimeError("Existing /send command group was not found.")

    if send_group.get_command("announcement") is None:

        @app_commands.command(
            name="announcement",
            description="Open the private Announcement Studio",
        )
        async def announcement_command(interaction: discord.Interaction):

            if interaction.user.id != OWNER_ID:
                await interaction.response.send_message(
                    "❌ You do not have permission to use this command.",
                    ephemeral=True,
                )
                return

            view = discord.ui.View(timeout=300)

            view.add_item(
                discord.ui.Button(
                    label="Open Announcement Studio",
                    emoji="🎨",
                    style=discord.ButtonStyle.link,
                    url=f"{BASE_URL}/announcement",
                )
            )

            await interaction.response.send_message(
                "🎨 **Announcement Studio**\n\n"
                "Open your private dashboard to create and publish announcements.",
                view=view,
                ephemeral=True,
            )

        send_group.add_command(announcement_command)

    logger.info("Announcement Studio extension loaded successfully.")
