import src.generate as _generate


def test___get_return_type__multiple_entity_collections():
    response_structure = {
        "AllianceService": {
            "ListUsers": {
              "Messages": {
                "Message": {}
              },
              "Users": {
                "User": {
                  "Alliance": {},
                  "UserSeason": {}
                }
              }
            }
        }
    }
    entity_names = ['Message', 'Ship', 'User']
    expected_result = ('ListUsers', [('Message', 'List'), ('Users', 'List')])

    assert _generate.__get_return_type(response_structure, entity_names) == expected_result


def test___get_return_type__single_entity_type():
    response_structure = {
        "AllianceService": {
            "ListAlliancesByRanking": {
              "Alliances": {
                "Alliance": {}
              }
            }
        }
    }
    entity_names = ['Alliance', 'ItemDesign', 'User']
    expected_result = ('Alliances', [('Alliance', 'List')])

    assert _generate.__get_return_type(response_structure, entity_names) == expected_result


def test___get_return_type__multiple_entity_types():
    
    response_structure = {
        "ShipService": {
            "InspectShip": {
                "Ship": {
                    "Characters": {},
                    "Items": {},
                    "Lifts": {},
                    "Researches": {
                        "Research": {}
                    },
                    "Rooms": {
                        "Room": {}
                    },
                    "UserStarSystems": {
                        "UserStarSystem": {}
                    }
                },
                "User": {}
            }
        }
    }
    entity_names = ['Alliance', 'Character', 'Item', 'Lift', 'Research', 'Ship', 'ShipDesign', 'User', 'UserStarSystem']
    expected_result = ('InspectShip', [('Ship', None), ('User', None)])

    assert _generate.__get_return_type(response_structure, entity_names) == expected_result