#!/usr/bin/env python3
"""
=============================================================================
MyNichePilot — Légendes & Hashtags des vidéos générées
=============================================================================
Fournit, pour chaque vidéo (5 séquences + master officiel), une légende
prête à publier sur les réseaux sociaux et une série de hashtags ciblés.

Ces données sont :
  1. exposées via l'API `/api/videos` (champs `caption` + `hashtags`) ;
  2. matérialisées dans le dossier `captions/` (un fichier Markdown par vidéo) ;
  3. copiables en un clic depuis l'interface VIP.

Auteur : MyNichePilot Creative Studio
=============================================================================
"""

# Chaque entrée est référencée par le nom de fichier MP4 généré.
VIDEO_CAPTIONS = {
    "sequence_1_hook.mp4": {
        "title": "Hook Choc — Surcharge Mentale",
        "caption": (
            "Et si la vraie raison pour laquelle tu n’as pas encore lancé ton business, "
            "c’était l’incertitude totale sur ta niche ? 🤯\n\n"
            "Trop d’idées, zéro plan clair, une surcharge mentale qui te paralyse. "
            "Ça change maintenant. 👇"
        ),
        "hashtags": [
            "#BusinessEnLigne", "#Entrepreneuriat", "#NicheRentable",
            "#SurchargeMentale", "#Solopreneur", "#MyNichePilot",
        ],
    },
    "sequence_2_probleme_solution.mp4": {
        "title": "Problème & Solution — Coach IA d’Exécution",
        "caption": (
            "Analyser la concurrence te prend des semaines ? 📉\n"
            "Le risque d’échec te freine avant même de commencer ?\n\n"
            "Voici NichePilot, le coach IA d’exécution business qui change la donne. 🎯"
        ),
        "hashtags": [
            "#CoachIA", "#IntelligenceArtificielle", "#BusinessOnline",
            "#AnalyseConcurrence", "#Execution", "#MyNichePilot",
        ],
    },
    "sequence_3_demonstration_saas.mp4": {
        "title": "Démonstration SaaS — Cockpit & Roadmap",
        "caption": (
            "Diagnostic en direct ✅\n"
            "Score de potentiel 94/100 ✅\n"
            "Roadmap concrète sur 16 semaines ✅\n\n"
            "Tout ce qu’il te faut pour valider ta niche, dans un seul cockpit. Regarde. 📊"
        ),
        "hashtags": [
            "#SaaS", "#DiagnosticBusiness", "#Roadmap",
            "#OpportunitesRentables", "#Cockpit", "#MyNichePilot",
        ],
    },
    "sequence_4_transformation.mp4": {
        "title": "Transformation — De la Confusion à la Clarté",
        "caption": (
            "Du doute à la certitude absolue en un instant 🚀\n"
            "Ta niche est validée, et ton offre irrésistible est prête à vendre.\n\n"
            "Le flou, c’est terminé."
        ),
        "hashtags": [
            "#Transformation", "#Clarte", "#OffreIrresistible",
            "#ValidationDeNiche", "#Entrepreneur", "#MyNichePilot",
        ],
    },
    "sequence_5_call_to_action.mp4": {
        "title": "Appel à l’Action — Diagnostic Gratuit",
        "caption": (
            "Ne laisse plus tes idées au placard. 🔥\n"
            "Rends-toi sur mynichepilot.com, fais ton diagnostic GRATUIT "
            "et lance enfin ton business.\n\nC’est maintenant ou jamais."
        ),
        "hashtags": [
            "#CallToAction", "#DiagnosticGratuit", "#LanceTonBusiness",
            "#Opportunite", "#Gratuit", "#MyNichePilot",
        ],
    },
    "MyNichePilot_Publicite_Officielle_9x16.mp4": {
        "title": "Master Officiel — Publicité 9:16",
        "caption": (
            "🎬 La publicité officielle complète MyNichePilot est là.\n\n"
            "44 secondes pour passer de la confusion à un business en ligne "
            "validé et prêt à vendre. Regarde, puis agis → mynichepilot.com"
        ),
        "hashtags": [
            "#MyNichePilot", "#PubliciteVideo", "#CoachIA",
            "#BusinessEnLigne", "#Entrepreneuriat", "#NicheRentable",
            "#DiagnosticGratuit",
        ],
    },
}

# Ordre d'affichage (les séquences puis le master en fin)
CAPTION_ORDER = [
    "sequence_1_hook.mp4",
    "sequence_2_probleme_solution.mp4",
    "sequence_3_demonstration_saas.mp4",
    "sequence_4_transformation.mp4",
    "sequence_5_call_to_action.mp4",
    "MyNichePilot_Publicite_Officielle_9x16.mp4",
]


def get_caption_info(filename):
    """Retourne (title, caption, hashtags, hashtags_str) pour un fichier vidéo."""
    entry = VIDEO_CAPTIONS.get(filename)
    if not entry:
        return None
    hashtags = entry.get("hashtags", [])
    return {
        "title": entry["title"],
        "caption": entry["caption"],
        "hashtags": hashtags,
        "hashtags_str": " ".join(hashtags),
    }


def build_social_text(filename):
    """Construit le texte global prêt à publier (légende + hashtags)."""
    info = get_caption_info(filename)
    if not info:
        return None
    parts = [info["caption"].rstrip()]
    if info["hashtags_str"]:
        parts.append("")
        parts.append(info["hashtags_str"])
    return "\n".join(parts)


if __name__ == "__main__":
    for fn in CAPTION_ORDER:
        text = build_social_text(fn)
        print("=" * 70)
        print(fn)
        print("=" * 70)
        print(text)
        print()