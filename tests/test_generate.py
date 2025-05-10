from typing import Dict as _Dict
from typing import List as _List
from typing import Tuple as _Tuple

import src.generate as _generate


def test___get_return_type__multiple_entity_collections():
    response_structure = {
        "AllianceService": {
            "ListUsers": {
                "Messages": {"Message": {}},
                "Users": {"User": {"Alliance": {}, "UserSeason": {}}},
            }
        }
    }
    entity_names = ["Message", "Ship", "User"]
    expected_result = (
        "ListUsers",
        [("Message", "Messages", True), ("User", "Users", True)],
    )

    result = _generate.__get_return_type(response_structure, entity_names)
    assert __return_type_tuples_equal(result, expected_result)


def test___get_return_type__single_entity_collection():
    response_structure = {
        "AllianceService": {"ListAlliancesByRanking": {"Alliances": {"Alliance": {}}}}
    }
    entity_names = ["Alliance", "ItemDesign", "User"]
    expected_result = ("Alliances", [("Alliance", "Alliances", True)])

    result = _generate.__get_return_type(response_structure, entity_names)
    assert __return_type_tuples_equal(result, expected_result)


def test___get_return_type__multiple_entity_types():

    response_structure = {
        "ShipService": {
            "InspectShip": {
                "Ship": {
                    "Characters": {},
                    "Items": {},
                    "Lifts": {},
                    "Researches": {"Research": {}},
                    "Rooms": {"Room": {}},
                    "UserStarSystems": {"UserStarSystem": {}},
                },
                "User": {},
            }
        }
    }
    entity_names = [
        "Alliance",
        "Character",
        "Item",
        "Lift",
        "Research",
        "Ship",
        "ShipDesign",
        "User",
        "UserStarSystem",
    ]
    expected_result = (
        "InspectShip",
        [("Ship", "InspectShip", False), ("User", "InspectShip", False)],
    )

    result = _generate.__get_return_type(response_structure, entity_names)
    assert __return_type_tuples_equal(result, expected_result)


def test___get_return_type__multiple_entity_types_and_collections():
    response_structure = {
        "DummyService": {
            "DummyEndpoint": {
                "Ship": {
                    "Characters": {},
                    "Items": {},
                    "Lifts": {},
                    "Researches": {"Research": {}},
                    "Rooms": {"Room": {}},
                    "UserStarSystems": {"UserStarSystem": {}},
                },
                "Users": {"User": {}},
            }
        }
    }
    entity_names = [
        "Alliance",
        "Character",
        "Item",
        "Lift",
        "Research",
        "Ship",
        "ShipDesign",
        "User",
        "UserStarSystem",
    ]
    expected_result = (
        "DummyEndpoint",
        [("Ship", "DummyEndpoint", False), ("User", "Users", True)],
    )

    result = _generate.__get_return_type(response_structure, entity_names)
    assert __return_type_tuples_equal(result, expected_result)


def test___get_return_type__get_latest_version_3():
    response_structure = {"SettingService": {"GetLatestSetting": {"Setting": {}}}}
    entity_names = ["Setting"]
    expected_result = ("GetLatestSetting", [("Setting", "GetLatestSetting", False)])

    result = _generate.__get_return_type(response_structure, entity_names)
    assert __return_type_tuples_equal(result, expected_result)


def test___get_return_type_for_python__multiple_entity_collections():
    return_types = [("Message", "Messages", True), ("User", "Users", True)]
    expected_result = "_Tuple[_List[_Message], _List[_User]]"
    assert _generate.__get_return_type_for_python(return_types) == expected_result


def test___get_return_type_for_python__multiple_entity_types():
    return_types = [("Ship", "InspectShip", False), ("User", "InspectShip", False)]
    expected_result = "_Tuple[_Ship, _User]"
    assert _generate.__get_return_type_for_python(return_types) == expected_result


def test___get_return_type_for_python__multiple_entity_types_and_collections():
    return_types = [("Ship", "DummyEndpoint", False), ("User", "Users", True)]
    expected_result = "_Tuple[_Ship, _List[_User]]"
    assert _generate.__get_return_type_for_python(return_types) == expected_result


def test___get_return_type_for_python__single_entity_collection():
    return_types = [("Alliance", "Alliances", True)]
    expected_result = "_List[_Alliance]"
    assert _generate.__get_return_type_for_python(return_types) == expected_result


def __return_type_tuples_equal(
    d1: _Tuple[str, _List[_Tuple[str, str, bool]]],
    d2: _Tuple[str, _List[_Tuple[str, str, bool]]],
) -> bool:
    if not d1 and not d2:
        return True
    if not d1 or not d2:
        return False
    if len(d1) != len(d2):
        return False

    try:
        if d1[0] != d2[0]:
            return False
        if len(d1[1]) != len(d2[1]):
            return False
        for i in range(len(d1[1])):
            if d1[1][i] != d2[1][i]:
                return False

        return True
    except:
        return False
