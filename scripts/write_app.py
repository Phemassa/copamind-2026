"""Script auxiliar: escreve o app.py do CopaMind 2026."""
# Execute: python scripts/write_app.py

APP = r'''"""CopaMind 2026 — Dashboard
Páginas: Seleções | Jogadores | Estatísticas | Bolão das LLMs
"""
from __future__ import annotations
import os
from datetime import UTC, datetime

import pandas as pd
import streamlit as st

from copamind.core.config import get_settings
from copamind.data.connectors.flags import TEAMS
from copamind.data.repositories import DuckDBRepository
from copamind.pool.service import leaderboard, lock_match_predictions, run_backtest
from copamind.pool.scoring import outcome
from copamind.ui.styles import CSS

ACCENT = "#52e3b5"
PANEL = "rgba(16,26,26,.92)"
LINE = "#1e3232"
STAGE_ORDER = {"group":1,"round_of_32":2,"round_of_16":3,
    "quarterfinal":4,"semifinal":5,"third_place":6,"final":7}
STAGE_PT = {"group":"Grupo","round_of_32":"2ª rodada","round_of_16":"Oitavas",
    "quarterfinal":"Quartas","semifinal":"Semifinal",
    "third_place":"3º Lugar","final":"Final","friendly":"Amistoso"}

@st.cache_resource
def _db_path(): return str(get_settings().duckdb_path)
def _repo():
    r = DuckDBRepository(_db_path()); r.create_schema(); return r
def _tinfo(tid, loc="pt-BR"):
    t = TEAMS.get(tid, {})
    return {"emoji":t.get("emoji","🏳"),"name":t.get("name_pt" if loc=="pt-BR" else "name_en",tid),
            "group":t.get("group","?"),"iso2":t.get("iso2","")}
def _copa_stats(repo, tid):
    w=d=l=gf=ga=best=0
    for m in repo.list_finished_matches():
        ih = m.home_team_id==tid; ia = m.away_team_id==tid
        if not ih and not ia: continue
        h,a=m.home_score or 0,m.away_score or 0
        gf+=h if ih else a; ga+=a if ih else h
        if ih:
            if h>a: w+=1
            elif h==a: d+=1
            else: l+=1
        else:
            if a>h: w+=1
            elif a==h: d+=1
            else: l+=1
        best=max(best,STAGE_ORDER.get(m.stage.value,0))
    return {"w":w,"d":d,"l":l,"gf":gf,"ga":ga,"pts":w*3+d,"gd":gf-ga,"stage":best}

def _inject(bg=""):
    st.markdown(CSS, unsafe_allow_html=True)
    if bg and os.path.exists(bg):
        import base64
        data=base64.b64encode(open(bg,"rb").read()).decode()
        st.markdown(f"""<style>
[data-testid="stApp"]{{background-image:url("data:image/png;base64,{data}") !important;
background-size:cover !important;background-attachment:fixed !important;}}
[data-testid="stApp"]::before{{content:"";position:fixed;inset:0;
background:linear-gradient(180deg,rgba(5,10,12,.7),rgba(5,10,12,.93));
pointer-events:none;z-index:0;}}</style>""", unsafe_allow_html=True)

def _sidebar():
    for img,w in [("docs/assets/icon.png",52),("docs/assets/copamind_2026.png",180)]:
        if os.path.exists(img): st.sidebar.image(img,width=w)
    st.sidebar.markdown("---")
    pg=st.sidebar.radio("Navegar",
        ["🏆 Seleções","⭐ Jogadores","📊 Estatísticas","🤖 Bolão das LLMs"],
        label_visibility="collapsed")
    st.sidebar.markdown("---")
    st.sidebar.caption("Previsões educacionais e experimentais. Copa 2026.")
    return pg

# ─── SELEÇÕES ────────────────────────────────────────────────────────────────
def render_selecoes():
    _inject("docs/assets/fundo_clean2.png")
    st.markdown("<div style='color:#52e3b5;font-size:11px;font-weight:900;"
        "letter-spacing:.2em;text-transform:uppercase'>Copa do Mundo 2026</div>",
        unsafe_allow_html=True)
    st.markdown("## 🏆 Seleções")
    repo=_repo(); teams=repo.list_teams()
    if not teams: st.warning("Sem dados. Rode: `copamind ingest sample`"); return
    all_s=[]
    for t in teams:
        ti=_tinfo(t.team_id); s=_copa_stats(repo,t.team_id)
        sn=next((STAGE_PT[k] for k,v in STAGE_ORDER.items() if v==s["stage"]),"Grupo")
        all_s.append({**ti,"team_id":t.team_id,**s,"stage_name":sn,
            "elim": s["stage"]>=3 or s["l"]>0})
    c1,c2,c3=st.columns([2,2,3])
    ft=c1.selectbox("Filtro",["Todas","Ainda na copa","Eliminadas"],label_visibility="collapsed")
    gr=c2.selectbox("Grupo",["Todos"]+sorted({t["group"] for t in all_s}),label_visibility="collapsed")
    if ft=="Ainda na copa": all_s=[t for t in all_s if not t["elim"]]
    elif ft=="Eliminadas": all_s=[t for t in all_s if t["elim"]]
    if gr!="Todos": all_s=[t for t in all_s if t["group"]==gr]
    all_s.sort(key=lambda x:(-x["stage"],-x["pts"],-x["gd"],-x["gf"]))
    for ri in range(0,len(all_s),4):
        row=all_s[ri:ri+4]; cols=st.columns(4)
        for ci,t in enumerate(row):
            sc="#19e3c2" if not t["elim"] else "#ff8c72"
            with cols[ci]:
                st.markdown(f"""<div style="background:{PANEL};border:1px solid {sc}40;
border-top:3px solid {sc};border-radius:14px;padding:14px;margin-bottom:8px;text-align:center">
<div style="font-size:34px">{t['emoji']}</div>
<div style="font-weight:800;font-size:14px;color:#f2faf8;margin:4px 0">{t['name']}</div>
<div style="background:{sc}22;color:{sc};border-radius:20px;padding:2px 10px;
font-size:10px;font-weight:700;display:inline-block;margin-bottom:8px">{t['stage_name']}</div>
<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:4px;font-size:11px;color:#9eb5b1">
<div><div style="color:#f2faf8;font-weight:700;font-size:16px">{t['w']}</div>V</div>
<div><div style="color:#f2faf8;font-weight:700;font-size:16px">{t['d']}</div>E</div>
<div><div style="color:#f2faf8;font-weight:700;font-size:16px">{t['l']}</div>D</div>
</div><div style="margin-top:8px;font-size:11px;color:#9eb5b1">
{t['gf']} gols · {t['ga']} sofridos · SG {t['gd']:+d}</div></div>""",
                    unsafe_allow_html=True)

# ─── JOGADORES ───────────────────────────────────────────────────────────────
def render_jogadores():
    _inject("docs/assets/fundo_clean1.png")
    st.markdown("## ⭐ Jogadores da Copa 2026")
    repo=_repo()
    if repo.count("player_ratings")==0:
        st.info("Carregue: `copamind ingest players data/samples/copa2026_players.json`")
        return
    t1,t2,t3=st.tabs(["🥇 Artilheiros","⭐ Top Ratings","🔍 Elenco"])
    with t1: _scorers(repo)
    with t2: _top_ratings(repo)
    with t3: _squad(repo)

def _scorers(repo):
    ps=repo.top_scorers(limit=25); rows=[]
    medals=["🥇","🥈","🥉"]
    for i,p in enumerate(ps,1):
        t=_tinfo(p.team_id); m=medals[i-1] if i<=3 else str(i)
        rows.append({"#":m,"Jogador":p.name,"Seleção":f"{t['emoji']} {t['name']}",
            "Pos":p.position,"⚽":p.copa_goals,"🎯":p.copa_assists,
            "🎮":p.copa_matches,"OVR":p.overall})
    if rows: st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

def _top_ratings(repo):
    ps=repo.list_players(limit=20)
    attrs=["pace","shooting","passing","dribbling","defending","physical"]
    labels=["PAC","SHO","PAS","DRI","DEF","PHY"]
    cols=st.columns(4)
    for ci,p in enumerate(ps):
        t=_tinfo(p.team_id)
        cc="#19e3c2" if p.overall>=88 else "#f6c453" if p.overall>=84 else "#4895ff"
        bars="".join([f"<div style='display:flex;align-items:center;gap:5px;font-size:10px'>"
            f"<span style='width:26px;color:#9eb5b1'>{lb}</span>"
            f"<div style='flex:1;background:#1e3232;border-radius:3px;height:5px'>"
            f"<div style='width:{getattr(p,at)}%;background:{cc};height:5px;border-radius:3px'></div>"
            f"</div><span style='width:22px;text-align:right;color:#f2faf8;font-weight:700'>"
            f"{getattr(p,at)}</span></div>" for lb,at in zip(labels,attrs)])
        with cols[ci%4]:
            st.markdown(f"""<div style="background:{PANEL};border:1px solid {LINE};
border-radius:12px;padding:12px;margin-bottom:10px">
<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
<div style="font-size:26px;font-weight:900;color:{cc}">{p.overall}</div>
<div><div style="font-weight:700;font-size:12px;color:#f2faf8">{p.name}</div>
<div style="font-size:10px;color:#9eb5b1">{t['emoji']} {p.position} · {p.age}a</div></div>
</div>{bars}<div style="margin-top:8px;font-size:10px;color:#9eb5b1;
border-top:1px solid {LINE};padding-top:6px">
⚽ {p.copa_goals}g · 🎯 {p.copa_assists}a · 🎮 {p.copa_matches} jogos</div></div>""",
                unsafe_allow_html=True)

def _squad(repo):
    teams=repo.list_teams()
    opts={f"{_tinfo(t.team_id)['emoji']} {_tinfo(t.team_id)['name']}":t.team_id for t in teams}
    sel=st.selectbox("Seleção",sorted(opts.keys()))
    tid=opts[sel]; ps=repo.list_players(team_id=tid)
    if not ps: st.info("Sem jogadores."); return
    PO={"GK":0,"CB":1,"RB":2,"LB":3,"CDM":4,"CM":5,"CAM":6,"RW":7,"LW":8,"CF":9,"ST":10}
    ps=sorted(ps,key=lambda p:PO.get(p.position,99))
    rows=[{"Pos":p.position,"Jogador":p.name,"Idade":p.age,"OVR":p.overall,
        "PAC":p.pace,"SHO":p.shooting,"PAS":p.passing,"DRI":p.dribbling,
        "DEF":p.defending,"PHY":p.physical,"⚽":p.copa_goals,"🎯":p.copa_assists} for p in ps]
    st.dataframe(pd.DataFrame(rows).style.background_gradient(
        subset=["OVR"],cmap="RdYlGn",vmin=60,vmax=99),
        use_container_width=True,hide_index=True)

# ─── ESTATÍSTICAS ────────────────────────────────────────────────────────────
def render_estatisticas():
    _inject()
    st.markdown("## 📊 Estatísticas — Copa 2026")
    repo=_repo(); fin=repo.list_finished_matches()
    if not fin: st.warning("Sem partidas."); return
    total_g=sum((m.home_score or 0)+(m.away_score or 0) for m in fin)
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Partidas",len(fin)); c2.metric("Gols",total_g)
    c3.metric("Média gols/jogo",f"{total_g/len(fin):.2f}"); c4.metric("Seleções",repo.count("teams"))
    st.markdown("---")
    st.markdown("### Fase de Grupos")
    grps=sorted({_tinfo(t.team_id)["group"] for t in repo.list_teams() if _tinfo(t.team_id)["group"]!="?"})
    cols=st.columns(3)
    for gi,g in enumerate(grps):
        with cols[gi%3]:
            with st.expander(f"Grupo {g}",expanded=False):
                tids=[t.team_id for t in repo.list_teams() if _tinfo(t.team_id)["group"]==g]
                rows=[]
                for tid in tids:
                    s=_copa_stats(repo,tid); ti=_tinfo(tid)
                    rows.append({"Seleção":f"{ti['emoji']} {ti['name']}",
                        "J":s["w"]+s["d"]+s["l"],"Pts":s["pts"],
                        "V":s["w"],"E":s["d"],"D":s["l"],
                        "GP":s["gf"],"GC":s["ga"],"SG":s["gd"]})
                rows.sort(key=lambda r:(-r["Pts"],-r["SG"],-r["GP"]))
                st.dataframe(pd.DataFrame(rows).set_index("Seleção"),use_container_width=True)
    st.markdown("---")
    st.markdown("### Resultados — Mata-mata")
    ko=["round_of_16","quarterfinal","semifinal","final","third_place"]
    ko_m=sorted([m for m in fin if m.stage.value in ko],key=lambda m:m.match_date,reverse=True)
    if ko_m:
        rows=[]
        for m in ko_m:
            h=_tinfo(m.home_team_id); a=_tinfo(m.away_team_id)
            hs,as_=m.home_score or 0,m.away_score or 0
            w="⬅" if hs>as_ else "➡" if as_>hs else "="
            rows.append({"Data":m.match_date.strftime("%d/%m"),"Fase":STAGE_PT.get(m.stage.value,""),
                "Casa":f"{h['emoji']} {h['name']}","Placar":f"{hs}–{as_} {w}",
                "Fora":f"{a['emoji']} {a['name']}"})
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

# ─── BOLÃO DAS LLMs ──────────────────────────────────────────────────────────
def render_bolao():
    _inject("docs/assets/fundo_clean1.png")
    st.markdown("<div style='color:#52e3b5;font-size:11px;font-weight:900;"
        "letter-spacing:.2em;text-transform:uppercase'>Benchmark de IAs Locais</div>",
        unsafe_allow_html=True)
    st.markdown("## 🤖 Bolão das LLMs")
    st.caption("Cada modelo prevê placar + vencedor antes do apito. "
               "ML roda silenciosamente; LLMs via LM Studio. Quem acertar mais ganha.")
    repo=_repo()
    t1,t2,t3=st.tabs(["⚡ Jogos & Palpites","🏆 Leaderboard","📜 Histórico"])
    with t1: _bolao_live(repo)
    with t2: _bolao_board(repo)
    with t3: _bolao_hist(repo)

def _bolao_live(repo):
    from copamind.pool.predictors import EloPredictor, PoissonPredictor
    ml_preds=[PoissonPredictor(),EloPredictor()]
    sched=[m for m in repo.list_matches(limit=500) if m.status.value=="scheduled"]
    if not sched: st.success("🏁 Todas as partidas com resultado!"); return
    by_s={}
    for m in sched:
        s=STAGE_PT.get(m.stage.value,m.stage.value)
        by_s.setdefault(s,[]).append(m)
    for stage,matches in sorted(by_s.items(),
            key=lambda x:STAGE_ORDER.get(next((k for k,v in STAGE_PT.items() if v==x[0]),""),99)):
        st.markdown(f"**{stage}**")
        for match in matches:
            _match_card(repo,match,ml_preds)
        st.markdown("---")

def _match_card(repo,match,ml_preds):
    h=_tinfo(match.home_team_id); a=_tinfo(match.away_team_id)
    ds=match.match_date.strftime("%d/%m %H:%M") if match.match_date else ""
    st.markdown(f"""<div style="margin:12px 0 6px">
<span style="color:{ACCENT};font-size:11px;font-weight:700;letter-spacing:.15em;
text-transform:uppercase">{ds}</span>
<strong style="font-size:17px;margin-left:10px">
{h['emoji']} {h['name']} × {a['emoji']} {a['name']}</strong></div>""",
        unsafe_allow_html=True)
    exist={p.predictor_name:p for p in repo.list_pool_predictions() if p.match_id==match.match_id}
    b1,b2,_=st.columns([2,2,4])
    if b1.button("▶ Palpites ML",key=f"ml_{match.match_id}"):
        new=lock_match_predictions(repo,match,ml_preds)
        st.success(f"{len(new)} palpites gerados!" if new else "Palpites já gerados.")
        st.rerun()
    if b2.button("🤖 Pedir às LLMs",key=f"llm_{match.match_id}"):
        _gen_llm(repo,match)
        st.rerun()
    if exist: _pred_cards(exist,h,a)
    else: st.caption("Clique em '▶ Palpites ML' para gerar previsões.")
    with st.expander(f"📝 Registrar placar"):
        with st.form(f"r_{match.match_id}"):
            r1,r2,r3=st.columns([3,1,3])
            r1.markdown(f"**{h['emoji']} {h['name']}**")
            hs=r1.number_input("Casa",0,20,0,key=f"hs_{match.match_id}")
            r2.markdown("<div style='text-align:center;padding-top:28px'>×</div>",unsafe_allow_html=True)
            aws=r3.number_input("Fora",0,20,0,key=f"as_{match.match_id}")
            r3.markdown(f"**{a['emoji']} {a['name']}**")
            if st.form_submit_button("💾 Salvar",use_container_width=True):
                _save(repo,match.match_id,int(hs),int(aws))
                st.success(f"✅ {h['name']} {hs}–{aws} {a['name']}"); st.rerun()

def _pred_cards(preds,h,a):
    cols=st.columns(min(len(preds),5))
    for ci,(nm,pred) in enumerate(preds.items()):
        c="#52e3b5" if "poisson" in nm else "#f6c453" if "elo" in nm else "#8e7cff"
        tag="ML Poisson" if "poisson" in nm else "ML Elo" if "elo" in nm else "LLM"
        wc=c if pred.prob_home>pred.prob_away else "#9eb5b1"
        lc=c if pred.prob_away>pred.prob_home else "#9eb5b1"
        with cols[ci%len(cols)]:
            st.markdown(f"""<div style="background:rgba(12,20,20,.95);
border:1px solid {LINE};border-top:3px solid {c};
border-radius:12px;padding:12px;margin-bottom:6px">
<div style="display:flex;justify-content:space-between;margin-bottom:6px">
<span style="color:{c};font-size:9px;font-weight:900;letter-spacing:.1em;
text-transform:uppercase">{tag}</span></div>
<div style="font-size:11px;font-weight:700;color:#f2faf8;margin-bottom:8px;
white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{nm}</div>
<div style="display:flex;justify-content:space-around;
background:rgba(255,255,255,.04);border-radius:8px;padding:8px">
<div style="text-align:center">
<div style="font-size:20px">{h['emoji']}</div>
<div style="color:{wc};font-size:18px;font-weight:900">{pred.prob_home:.0%}</div>
</div>
<div style="text-align:center">
<div style="color:#9eb5b1;font-size:12px;font-weight:700">{pred.prob_draw:.0%}</div>
<div style="color:#9eb5b1;font-size:9px">Emp</div>
</div>
<div style="text-align:center">
<div style="font-size:20px">{a['emoji']}</div>
<div style="color:{lc};font-size:18px;font-weight:900">{pred.prob_away:.0%}</div>
</div>
</div>
<div style="text-align:center;margin-top:8px;font-size:14px;color:{c};font-weight:700">
{pred.predicted_home_goals}–{pred.predicted_away_goals}</div>
</div>""", unsafe_allow_html=True)

def _gen_llm(repo,match):
    try:
        from copamind.llm.client import LMStudioClient
        from copamind.llm.config import load_model_specs
        from copamind.pool.predictors import LLMPredictor
        settings=get_settings(); specs=load_model_specs()
        client=LMStudioClient(base_url=settings.lmstudio_base_url,
            api_key=settings.lmstudio_api_key,
            timeout=float(settings.lmstudio_timeout_seconds))
        preds=[LLMPredictor(client,specs[r].model_id,
            name=f"llm:{specs[r].model_id.split('/')[-1]}")
            for r in ("analyst","challenger") if r in specs]
        if preds:
            new=lock_match_predictions(repo,match,preds)
            st.success(f"🤖 {len(new)} palpites de LLMs!")
        else: st.warning("Configure models.yaml.")
    except Exception as e: st.warning(f"LM Studio indisponível: {e}")

def _save(repo,mid,hs,aws):
    from copamind.data.schemas import MatchStatus, PoolResult
    repo._con.execute("UPDATE matches SET home_score=?,away_score=?,status=? WHERE match_id=?",
        [hs,aws,str(MatchStatus.finished),mid])
    repo.upsert_pool_result(PoolResult(match_id=mid,home_score=hs,away_score=aws,
        recorded_at=datetime.now(UTC)))

def _bolao_board(repo):
    if st.button("🔄 Recalcular"):
        standings=run_backtest(repo).standings
    else:
        standings=leaderboard(repo)
    if not standings:
        st.info("Sem palpites pontuados. Gere palpites e registre resultados."); return
    mc=["#f6c453","#c7d4d2","#d89567"]; mm=["🥇","🥈","🥉"]
    cols=st.columns(min(len(standings),4))
    for i,s in enumerate(standings):
        c=mc[i] if i<3 else ACCENT; m=mm[i] if i<3 else f"#{i+1}"
        with cols[i%len(cols)]:
            st.markdown(f"""<div style="border:1px solid {c};border-top:4px solid {c};
border-radius:14px;padding:18px;background:{PANEL};text-align:center;margin-bottom:10px">
<div style="font-size:28px">{m}</div>
<div style="font-size:15px;font-weight:800;color:#f2faf8;margin:8px 0 4px">{s.predictor_name}</div>
<div style="font-size:36px;font-weight:900;color:{c}">{s.total_points}</div>
<div style="color:#9eb5b1;font-size:11px;margin-bottom:10px">pontos</div>
<hr style="border-color:{LINE}">
<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:4px;font-size:11px;margin-top:8px">
<div><div style="color:#9eb5b1">Palpites</div><strong>{s.predictions}</strong></div>
<div><div style="color:#9eb5b1">Placar certo</div><strong>{s.exact_scores}</strong></div>
<div><div style="color:#9eb5b1">Brier</div><strong>{s.mean_brier:.3f}</strong></div>
</div></div>""", unsafe_allow_html=True)
    if len(standings)>4:
        rows=[{"#":i+1,"Preditor":s.predictor_name,"Pts":s.total_points,
            "Palpites":s.predictions,"Placar certo":s.exact_scores,
            "Resultado certo":s.correct_results,"Brier":f"{s.mean_brier:.3f}"}
            for i,s in enumerate(standings)]
        st.markdown("---")
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

def _bolao_hist(repo):
    from copamind.pool.scoring import bolao_points, brier_score
    results={r.match_id:r for r in repo.list_pool_results()}
    preds=repo.list_pool_predictions()
    if not results: st.info("Sem resultados registrados ainda."); return
    by_m={}
    for p in preds:
        if p.match_id not in results: continue
        by_m.setdefault(p.match_id,{"preds":[],"res":results[p.match_id]})
        by_m[p.match_id]["preds"].append(p)
    all_m=repo.list_matches(limit=500)
    mmap={m.match_id:m for m in all_m}
    for mid,data in sorted(by_m.items(),reverse=True):
        res=data["res"]; act=outcome(res.home_score,res.away_score)
        m_obj=mmap.get(mid)
        if m_obj:
            h=_tinfo(m_obj.home_team_id); a=_tinfo(m_obj.away_team_id)
            title=f"{h['emoji']} {h['name']} **{res.home_score}–{res.away_score}** {a['emoji']} {a['name']}"
        else: title=f"Partida {mid}"
        with st.expander(title):
            rows=[]
            for p in data["preds"]:
                pts=bolao_points(p.predicted_home_goals,p.predicted_away_goals,res.home_score,res.away_score)
                br=brier_score(p.prob_home,p.prob_draw,p.prob_away,act)
                ic="✅" if pts==5 else "🟡" if pts==3 else "❌"
                rows.append({ic:ic,"Preditor":p.predictor_name,
                    "Palpite":f"{p.predicted_home_goals}–{p.predicted_away_goals}",
                    "Real":f"{res.home_score}–{res.away_score}","Pts":pts,"Brier":f"{br:.3f}"})
            if rows: st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

# ─── MAIN ────────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="CopaMind 2026",
        page_icon="docs/assets/icon.png" if os.path.exists("docs/assets/icon.png") else "⚽",
        layout="wide", initial_sidebar_state="expanded")
    pg=_sidebar()
    if pg=="🏆 Seleções": render_selecoes()
    elif pg=="⭐ Jogadores": render_jogadores()
    elif pg=="📊 Estatísticas": render_estatisticas()
    elif pg=="🤖 Bolão das LLMs": render_bolao()

if __name__=="__main__":
    main()
'''

with open("apps/streamlit/app.py", "w", encoding="utf-8") as f:
    f.write(APP)
print(f"Written: {len(APP)} chars")
