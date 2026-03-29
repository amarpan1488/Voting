import streamlit as st
import json
import os
import time
from datetime import datetime
from filelock import FileLock

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SCOS Executive Committee Election 2026",
    page_icon="⚕",
    layout="centered",
    initial_sidebar_state="collapsed",
)

VOTES_FILE = "votes.json"
LOCK_FILE  = "votes.json.lock"
PASSWORD   = "amarpan"

CANDIDATES = [
    {
        "id": "kadakia",
        "name": "Nimish Kadakia, MD",
        "specialty": "Sports Medicine & Arthroscopic Surgery",
        "photo": "https://assets.yourpractice.online/3003/nimisha-kadakiha-sb-img.png",
        "bio": [
            "I wanted to share my interest in serving on the Executive Committee and contributing in a more formal leadership role within our group.",
            "Over the years, I've had the opportunity to work within a variety of practice models, which has given me a broad perspective on how different group structures function and the needs they bring. I believe this has helped me develop a balanced and thoughtful approach when considering decisions that affect both our physicians and our patients.",
            "My experience serving as Chief of Orthopedics at Saddleback Hospital for the past four years has also allowed me to collaborate closely with multidisciplinary teams, navigate system-level challenges, and support both clinical and operational priorities.",
            "If selected, I would be committed to representing all of our satellite offices and ensuring their perspectives are heard and included. I also hope to bring a collaborative, practical, and well-rounded viewpoint that supports the continued growth and success of our group.",
            "Thank you for your time and consideration, and for all that you do each day.",
        ],
    },
    {
        "id": "veneziano",
        "name": "Christopher Veneziano, MD",
        "specialty": "Sports Medicine & Arthroscopic Surgery",
        "photo": "https://assets.yourpractice.online/3003/sb-christopher-img.png",
        "bio": [
            "With 20 years under my belt as a member of SCOS, I feel I'm ready to take on a more contributing role in the practice.",
            "I have experience in leadership and governance, collaboration and decision making serving two terms as Chief of Orthopedics at SMMC and serving two terms on the medical executive board of our Surgery Center.",
            "I'd like to be on the EC committee to help shape the future of our practice, advocate for my colleagues, support decisions that improve patient care, efficiency, and physician satisfaction.",
            "Appreciate your trust.",
        ],
    },
    {
        "id": "gurbani",
        "name": "Ajay Gurbani, MD",
        "specialty": "Foot & Ankle Surgery",
        "photo": "https://assets.yourpractice.online/3003/sb-gurbani-img.png",
        "bio": [
            "I would like to join the executive committee due to being one of the newest partners in the group. I think I do have a lot to learn about how the practice is run, and will come in with an open mind. However, I also think I can bring a fresh perspective and collaborative mindset.",
            "Also, as one of the surgeons going to multiple of the satellite offices, I think I can represent the interests and challenges that may be encountered at those locations as well.",
        ],
    },
]

POINT_MAP = {1: 3, 2: 2, 3: 1}


# ── Storage ───────────────────────────────────────────────────────────────────
def load_votes():
    if not os.path.exists(VOTES_FILE):
        return []
    with FileLock(LOCK_FILE):
        with open(VOTES_FILE, "r") as f:
            return json.load(f)


def save_vote(entry):
    with FileLock(LOCK_FILE):
        votes = []
        if os.path.exists(VOTES_FILE):
            with open(VOTES_FILE, "r") as f:
                votes = json.load(f)
        votes.append(entry)
        with open(VOTES_FILE, "w") as f:
            json.dump(votes, f, indent=2)


def clear_votes():
    with FileLock(LOCK_FILE):
        with open(VOTES_FILE, "w") as f:
            json.dump([], f)


# ── Session state defaults ────────────────────────────────────────────────────
def init_state():
    defaults = {
        "page": "name",          # name | vote | thanks | results
        "voter_name": "",
        "ranks": {},             # {candidate_id: 1|2|3}
        "read_bios": set(),      # set of candidate ids whose bio was opened
        "pwd_attempt": "",
        "pwd_error": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Source+Sans+3:wght@300;400;600&display=swap');

html, body, [class*="css"] { font-family: 'Source Sans 3', sans-serif; }

.header-bar {
    background: #0d2240; color: white;
    padding: 18px 28px; border-radius: 0;
    border-bottom: 3px solid #c9a84c;
    display: flex; align-items: center; gap: 16px;
    margin: -4rem -4rem 2rem -4rem;
}
.header-logo {
    width: 52px; height: 52px; background: #c9a84c; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-family: 'Playfair Display', serif; font-weight: 700;
    font-size: 20px; color: #0d2240; flex-shrink: 0;
}
.header-title { font-family: 'Playfair Display', serif; font-size: 1.3rem; font-weight: 600; margin: 0; }
.header-sub { font-size: 0.75rem; opacity: 0.7; letter-spacing: 0.08em; text-transform: uppercase; margin: 2px 0 0 0; }

h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: #0d2240 !important; }

.voter-badge {
    background: #0d2240; color: white; display: inline-block;
    padding: 6px 18px; border-radius: 20px; font-size: 0.85rem; margin-bottom: 12px;
}
.voter-badge b { color: #c9a84c; }

.instruction-box {
    background: linear-gradient(90deg, #0d2240, #163455);
    color: white; border-radius: 10px; padding: 16px 20px;
    font-size: 0.92rem; margin-bottom: 24px;
}
.instruction-box b { color: #e8c97a; }

.candidate-header {
    display: flex; align-items: center; gap: 14px; margin-bottom: 4px;
}
.candidate-header img {
    width: 72px; height: 72px; border-radius: 50%;
    object-fit: cover; object-position: top;
    border: 3px solid #c9a84c;
}
.candidate-initials {
    width: 72px; height: 72px; border-radius: 50%;
    background: #0d2240; display: flex; align-items: center; justify-content: center;
    font-family: 'Playfair Display', serif; font-size: 1.5rem;
    color: #c9a84c; font-weight: 700; flex-shrink: 0;
    border: 3px solid #c9a84c;
}
.c-name { font-family: 'Playfair Display', serif; font-size: 1.2rem; color: #0d2240; margin: 0; }
.c-title { color: #c9a84c; font-size: 0.78rem; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; margin: 2px 0 0 0; }

.rank-tag-1 { background: rgba(201,168,76,0.15); color: #8a6d00; padding: 2px 10px; border-radius: 12px; font-weight: 700; font-size: 0.82rem; }
.rank-tag-2 { background: rgba(156,163,175,0.2); color: #4b5563; padding: 2px 10px; border-radius: 12px; font-weight: 700; font-size: 0.82rem; }
.rank-tag-3 { background: rgba(180,83,9,0.12); color: #92400e; padding: 2px 10px; border-radius: 12px; font-weight: 700; font-size: 0.82rem; }

.result-bar-container { background: #ddd8cf; border-radius: 6px; height: 12px; overflow: hidden; margin: 6px 0 3px 0; }
.result-bar-fill { height: 100%; border-radius: 6px; background: #0d2240; }
.result-bar-fill-gold { height: 100%; border-radius: 6px; background: #c9a84c; }

.winner-tag { background: #c9a84c; color: #0d2240; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; padding: 3px 10px; border-radius: 12px; }

div[data-testid="stExpander"] { border: 1px solid #ddd8cf !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-bar">
  <div class="header-logo">S</div>
  <div>
    <p class="header-title">SCOS Executive Committee</p>
    <p class="header-sub">Board Member Election · 2026</p>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: NAME ENTRY
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == "name":
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## ⚕ Cast Your Vote")
        st.markdown("SCOS physicians are selecting two new Executive Committee board members. Please enter your name to access the ballot.")
        st.markdown("<br>", unsafe_allow_html=True)

        name = st.text_input("Your Name", placeholder="Dr. Jane Smith", key="name_input")
        if st.button("Continue to Ballot →", use_container_width=True, type="primary"):
            if len(name.strip()) < 2:
                st.error("Please enter your full name.")
            else:
                st.session_state.voter_name = name.strip()
                st.session_state.ranks = {}
                st.session_state.read_bios = set()
                st.session_state.page = "vote"
                st.rerun()

        st.markdown("<br><br>")
        if st.button("🔒 View Results (Admin)", use_container_width=False):
            st.session_state.page = "results_pwd"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: VOTING
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "vote":
    st.markdown(
        f'<div class="voter-badge">Voting as: <b>{st.session_state.voter_name}</b></div>',
        unsafe_allow_html=True,
    )
    st.markdown("## Executive Committee Ballot")
    st.markdown(
        '<div class="instruction-box">📋 You must <b>open each candidate\'s statement</b> before submitting. '
        'Then assign a unique rank of <b>1st</b>, <b>2nd</b>, and <b>3rd</b> to each candidate below.</div>',
        unsafe_allow_html=True,
    )

    # ── Candidate cards ──────────────────────────────────────────────────────
    for c in CANDIDATES:
        current_rank = st.session_state.ranks.get(c["id"])
        rank_color = ["", "#c9a84c", "#9ca3af", "#b45309"]
        border_color = rank_color[current_rank] if current_rank else "#ddd8cf"

        with st.container(border=True):
            # Photo + name row
            img_col, info_col = st.columns([1, 4])
            with img_col:
                st.image(c["photo"], width=80)
            with info_col:
                st.markdown(f'<p class="c-name">{c["name"]}</p><p class="c-title">{c["specialty"]}</p>', unsafe_allow_html=True)
                if current_rank:
                    labels = {1: "🥇 Ranked 1st", 2: "🥈 Ranked 2nd", 3: "🥉 Ranked 3rd"}
                    st.markdown(f'<span class="rank-tag-{current_rank}">{labels[current_rank]}</span>', unsafe_allow_html=True)

            # Bio expander — track when opened
            bio_label = "📖 Read Statement" if c["id"] not in st.session_state.read_bios else "✅ Statement Read"
            with st.expander(bio_label):
                st.session_state.read_bios.add(c["id"])
                for para in c["bio"]:
                    st.markdown(para)

        st.markdown("")

    # ── Ranking panel ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🗳 Your Rankings")
    st.markdown("Assign 1st, 2nd, and 3rd to each candidate. Each rank can only be used once.")
    st.markdown("")

    rank_options = ["— Not ranked —", "1st (3 pts)", "2nd (2 pts)", "3rd (1 pt)"]
    rank_values  = [None, 1, 2, 3]

    for c in CANDIDATES:
        r_col, n_col = st.columns([3, 2])
        with n_col:
            st.markdown(f"**{c['name'].split(',')[0]}**")
        with r_col:
            current = st.session_state.ranks.get(c["id"])
            current_idx = rank_values.index(current) if current in rank_values else 0

            # Disable options taken by other candidates
            taken = {v for k, v in st.session_state.ranks.items() if k != c["id"]}

            sel = st.selectbox(
                label=c["name"],
                options=rank_options,
                index=current_idx,
                key=f"sel_{c['id']}",
                label_visibility="collapsed",
            )
            new_rank = rank_values[rank_options.index(sel)]

            # Check for conflicts
            if new_rank is not None and new_rank in taken:
                st.warning(f"Rank {sel} is already assigned to another candidate.")
                new_rank = None
                sel = rank_options[0]

            if new_rank != st.session_state.ranks.get(c["id"]):
                if new_rank is None:
                    st.session_state.ranks.pop(c["id"], None)
                else:
                    st.session_state.ranks[c["id"]] = new_rank
                st.rerun()

    # ── Submit ────────────────────────────────────────────────────────────────
    st.markdown("---")
    unread = [c["name"].split()[0] for c in CANDIDATES if c["id"] not in st.session_state.read_bios]
    unranked = [c["name"].split()[0] for c in CANDIDATES if c["id"] not in st.session_state.ranks]

    if unread:
        st.warning(f"📋 Please read **{' & '.join(unread)}'s** statement{'s' if len(unread) > 1 else ''} before submitting.")
    elif unranked:
        st.info(f"Please rank **{' & '.join(unranked)}** before submitting.")
    else:
        st.success("✅ All statements read and all candidates ranked. Ready to submit!")

    submit_disabled = bool(unread or unranked)
    if st.button("Submit My Vote ✓", type="primary", disabled=submit_disabled, use_container_width=True):
        entry = {
            "name":      st.session_state.voter_name,
            "timestamp": datetime.now().strftime("%b %-d, %I:%M %p"),
            "kadakia":   st.session_state.ranks["kadakia"],
            "veneziano": st.session_state.ranks["veneziano"],
            "gurbani":   st.session_state.ranks["gurbani"],
        }
        save_vote(entry)
        st.session_state.page = "thanks"
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: THANK YOU
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "thanks":
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 🎉 Vote Recorded!")
        st.success(
            f"Thank you, **{st.session_state.voter_name}**. Your vote has been successfully submitted. "
            "The SCOS Executive Committee thanks you for your participation."
        )
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Back to Start", use_container_width=True):
            st.session_state.page = "name"
            st.session_state.voter_name = ""
            st.session_state.ranks = {}
            st.session_state.read_bios = set()
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: RESULTS PASSWORD
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "results_pwd":
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 🔐 Results Access")
        st.markdown("Enter the administrator password to view vote results.")
        pwd = st.text_input("Password", type="password", key="pwd_field")
        if st.button("View Results", type="primary", use_container_width=True):
            if pwd == PASSWORD:
                st.session_state.page = "results"
                st.rerun()
            else:
                st.error("Incorrect password. Please try again.")
        st.markdown("")
        if st.button("← Back"):
            st.session_state.page = "name"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: RESULTS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "results":
    votes = load_votes()
    pts = {c["id"]: 0 for c in CANDIDATES}
    for v in votes:
        for c in CANDIDATES:
            pts[c["id"]] += POINT_MAP.get(v.get(c["id"]), 0)

    sorted_candidates = sorted(CANDIDATES, key=lambda c: pts[c["id"]], reverse=True)
    max_pts = pts[sorted_candidates[0]["id"]] or 1

    st.markdown(f"## Election Results")
    st.markdown(f"*{len(votes)} vote{'s' if len(votes) != 1 else ''} cast · SCOS Executive Committee 2026*")
    st.markdown("---")

    for i, c in enumerate(sorted_candidates):
        is_winner = i < 2
        pct = int(pts[c["id"]] / max_pts * 100)

        with st.container(border=True):
            col_pos, col_img, col_info, col_bar = st.columns([0.5, 1, 3, 3])
            with col_pos:
                st.markdown(f"### {'🥇' if i==0 else '🥈' if i==1 else '🥉'}")
            with col_img:
                st.image(c["photo"], width=64)
            with col_info:
                st.markdown(f"**{c['name']}**")
                st.markdown(f"{pts[c['id']]} point{'s' if pts[c['id']] != 1 else ''}")
                if is_winner:
                    st.markdown('<span class="winner-tag">✓ Elected</span>', unsafe_allow_html=True)
            with col_bar:
                fill_class = "result-bar-fill-gold" if is_winner else "result-bar-fill"
                st.markdown(
                    f'<div class="result-bar-container"><div class="{fill_class}" style="width:{pct}%"></div></div>'
                    f'<small style="color:#6b7280">{pct}% of max</small>',
                    unsafe_allow_html=True,
                )

    # ── Vote log ──────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"### Individual Vote Log — {len(votes)} vote{'s' if len(votes) != 1 else ''}")

    if not votes:
        st.info("No votes recorded yet.")
    else:
        rank_labels = {1: "1st 🥇", 2: "2nd 🥈", 3: "3rd 🥉"}
        table_data = []
        for v in votes:
            table_data.append({
                "Voter": v["name"],
                "Kadakia":   rank_labels.get(v["kadakia"], "—"),
                "Veneziano": rank_labels.get(v["veneziano"], "—"),
                "Gurbani":   rank_labels.get(v["gurbani"], "—"),
                "Submitted": v["timestamp"],
            })
        st.dataframe(table_data, use_container_width=True, hide_index=True)

    st.markdown("---")
    col_refresh, col_clear, col_back = st.columns([2, 2, 2])
    with col_refresh:
        if st.button("🔄 Refresh Results", use_container_width=True):
            st.rerun()
    with col_clear:
        if st.button("⚠ Clear All Votes", use_container_width=True):
            clear_votes()
            st.rerun()
    with col_back:
        if st.button("← Back to Voting", use_container_width=True):
            st.session_state.page = "name"
            st.rerun()
