{
    "name": "IKGA Seminar",
    "version": "0.1",
    "category": "Administration",
    "sequence": 1,
    "summary": "IKGA Seminar Management Tool",
    "description": "A collection of modules for the organization of the IKGA Event",

    "depends": [
        "contacts",
        "sale_management",
        "account"],

    "data": [
        "security/ir.model.access.csv",
        "views/registration_views.xml",
        "views/room_views.xml",
    ],
    "intallable": True,
    "application": True,
    "auto_install": False
}