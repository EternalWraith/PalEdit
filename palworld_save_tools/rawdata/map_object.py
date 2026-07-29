from typing import Any

from palworld_save_tools.archive import (
    FArchiveReader,
    FArchiveWriter,
    encoded_raw_data,
    without_custom_type,
)
from palworld_save_tools.rawdata import (
    build_process,
    connector,
    map_concrete_model,
    map_concrete_model_module,
    map_model,
)


def decode(
    reader: FArchiveReader, type_name: str, size: int, path: str
) -> dict[str, Any]:
    if type_name != "ArrayProperty":
        raise Exception(f"Expected ArrayProperty, got {type_name}")
    value = reader.property(type_name, size, path, nested_caller_path=path)
    for map_object in value["value"]["values"]:
        # Decode Model
        map_object["Model"]["value"]["RawData"]["value"] = map_model.decode_bytes(
            reader, map_object["Model"]["value"]["RawData"]["value"]["values"]
        )
        # Decode Model.Connector
        map_object["Model"]["value"]["Connector"]["value"]["RawData"]["value"] = (
            connector.decode_bytes(
                reader,
                map_object["Model"]["value"]["Connector"]["value"]["RawData"]["value"][
                    "values"
                ],
            )
        )
        # Decode Model.BuildProcess
        map_object["Model"]["value"]["BuildProcess"]["value"]["RawData"]["value"] = (
            build_process.decode_bytes(
                reader,
                map_object["Model"]["value"]["BuildProcess"]["value"]["RawData"][
                    "value"
                ]["values"],
            )
        )
        # Decode ConcreteModel
        map_object_id = map_object["MapObjectId"]["value"]
        map_object["ConcreteModel"]["value"]["RawData"]["value"] = (
            map_concrete_model.decode_bytes(
                reader,
                map_object["ConcreteModel"]["value"]["RawData"]["value"]["values"],
                map_object_id,
            )
        )
        # Decode ConcreteModel.ModuleMap
        for module in map_object["ConcreteModel"]["value"]["ModuleMap"]["value"]:
            module_type = module["key"]
            module_bytes = module["value"]["RawData"]["value"]["values"]
            module["value"]["RawData"]["value"] = (
                map_concrete_model_module.decode_bytes(
                    reader,
                    module_bytes,
                    module_type,
                )
            )
    return value


def encode(
    writer: FArchiveWriter, property_type: str, properties: dict[str, Any]
) -> int:
    if property_type != "ArrayProperty":
        raise Exception(f"Expected ArrayProperty, got {property_type}")

    map_objects = []
    for map_object in properties["value"]["values"]:
        model = map_object["Model"]["value"]
        connector_prop = model["Connector"]
        build_process_prop = model["BuildProcess"]
        encoded_model = {
            **model,
            "RawData": encoded_raw_data(model["RawData"], map_model.encode_bytes),
            "Connector": {
                **connector_prop,
                "value": {
                    **connector_prop["value"],
                    "RawData": encoded_raw_data(
                        connector_prop["value"]["RawData"], connector.encode_bytes
                    ),
                },
            },
            "BuildProcess": {
                **build_process_prop,
                "value": {
                    **build_process_prop["value"],
                    "RawData": encoded_raw_data(
                        build_process_prop["value"]["RawData"],
                        build_process.encode_bytes,
                    ),
                },
            },
        }

        concrete_model = map_object["ConcreteModel"]["value"]
        encoded_concrete_model = {
            **concrete_model,
            "RawData": encoded_raw_data(
                concrete_model["RawData"], map_concrete_model.encode_bytes
            ),
            "ModuleMap": {
                **concrete_model["ModuleMap"],
                "value": [
                    {
                        **module,
                        "value": {
                            **module["value"],
                            "RawData": encoded_raw_data(
                                module["value"]["RawData"],
                                map_concrete_model_module.encode_bytes,
                                module["key"],
                            ),
                        },
                    }
                    for module in concrete_model["ModuleMap"]["value"]
                ],
            },
        }

        map_objects.append(
            {
                **map_object,
                "Model": {**map_object["Model"], "value": encoded_model},
                "ConcreteModel": {
                    **map_object["ConcreteModel"],
                    "value": encoded_concrete_model,
                },
            }
        )

    properties = without_custom_type(properties)
    properties["value"] = {**properties["value"], "values": map_objects}
    return writer.property_inner(property_type, properties)
