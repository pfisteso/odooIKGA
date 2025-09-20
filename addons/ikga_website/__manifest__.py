{
    "name": "IKGA Website",
    "version": "0.1",
    "category": "Website/Website",
    "sequence": 1,
    "summary": "IKGA Seminar Website Extension",
    "description": "A collection of modules and web pages for the organization of the IKGA Event",

    "depends": [
        "ikga_seminar",
        "website"],

    "data": [
        "security/ir.model.access.csv",
        "views/registration_portal.xml",
        "views/registration_form.xml"
    ],
    "intallable": True,
    "application": False,
    "auto_install": False
}