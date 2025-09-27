{
    "name": "IKGA Seminar",
    "version": "0.1",
    "category": "Administration",
    "sequence": 1,
    "summary": "IKGA Seminar Management Tool",
    "description": "A collection of modules for the organization of the IKGA Event",

    "depends": [
        "account",
        "contacts",
        "sale_management"
    ],

    "data": [
        "security/ir.model.access.csv",
        "views/hotel_room_views.xml",
        "views/res_config_settings.xml",
        "views/registration_views.xml",
        "views/room_category.xml",
        "views/menu.xml",
        "views/mail_templates.xml",
        "views/cron.xml"
    ],
    "intallable": True,
    "application": True,
    "auto_install": False
}
