from __future__ import annotations

ALLOWED_TAGS: frozenset[str] = frozenset({
    # thematisch
    "lebensmittel", "restaurant", "cafe", "transport", "tanken",
    "wohnen", "nebenkosten", "strom", "internet", "versicherung",
    "gesundheit", "apotheke", "arzt", "kleidung", "elektronik",
    "haushalt", "freizeit", "sport", "reise", "bildung",
    "bücher", "software", "abonnement", "streaming",
    "gehalt", "freelance", "erstattung", "transfer",
    "investition", "sparen", "steuer", "geschenk",
    # bewertend
    "unnötig", "impuls", "ungesund", "tabak", "alkohol",
    "luxury", "wiederkehrend", "einmalig",
})
