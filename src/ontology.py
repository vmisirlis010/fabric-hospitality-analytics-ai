"""Fabric IQ ontology for Kyanos: Hotel, Airport, VipGuest, UpcomingStay, OpenCase, TourOperator."""
import random, uuid
from fab import part

VT = {"string": "String", "long": "BigInt", "double": "Double", "boolean": "Boolean"}
SCHEMAS = {
    "iq_hotel": [("hotel_id", "long"), ("hotel_code", "string"), ("hotel_name", "string"), ("destination", "string"), ("region", "string"), ("concept", "string"),
                 ("stars", "long"), ("rooms", "long"), ("airport_code", "string"), ("general_manager", "string"), ("occupancy_2026", "double"),
                 ("revpar_2026", "double"), ("revpar_vs_ly", "double"), ("avg_case_csat", "double"), ("open_cases", "long")],
    "iq_airport": [("airport_code", "string"), ("airport_name", "string"), ("airport_region", "string"), ("seat_growth_2026", "double"), ("seat_growth_2027", "double")],
    "iq_vip_guest": [("guest_id", "long"), ("guest_name", "string"), ("country", "string"), ("language", "string"), ("loyalty_tier", "string"),
                     ("member_id", "string"), ("lifetime_nights", "long"), ("top_preference", "string")],
    "iq_upcoming_stay": [("reservation_id", "long"), ("confirmation_no", "string"), ("hotel_id", "long"), ("guest_id", "long"), ("arrival_date", "string"),
                         ("nights", "long"), ("room_type", "string"), ("channel", "string"), ("board_type", "string"), ("room_revenue", "double"),
                         ("tour_operator_id", "string")],
    "iq_open_case": [("case_id", "string"), ("hotel_id", "long"), ("created_date", "string"), ("category", "string"), ("sub_category", "string"),
                     ("origin", "string"), ("status", "string"), ("csat_score", "long"), ("guest_id", "long")],
    "iq_tour_operator": [("tour_operator_id", "string"), ("tour_operator_name", "string"), ("home_market", "string"), ("room_nights_2026", "long"),
                         ("otb_room_nights_2027", "long")],
}
ENTITIES = [("Hotel", "iq_hotel", "hotel_id", "hotel_name"), ("Airport", "iq_airport", "airport_code", "airport_name"),
            ("VipGuest", "iq_vip_guest", "guest_id", "guest_name"), ("UpcomingStay", "iq_upcoming_stay", "reservation_id", "confirmation_no"),
            ("OpenCase", "iq_open_case", "case_id", "case_id"), ("TourOperator", "iq_tour_operator", "tour_operator_id", "tour_operator_name")]
RELS = [("served_by", "Hotel", "Airport", "iq_hotel", "hotel_id", "airport_code"),
        ("stays_at", "UpcomingStay", "Hotel", "iq_upcoming_stay", "reservation_id", "hotel_id"),
        ("booked_by", "UpcomingStay", "VipGuest", "iq_upcoming_stay", "reservation_id", "guest_id"),
        ("sold_by", "UpcomingStay", "TourOperator", "iq_upcoming_stay", "reservation_id", "tour_operator_id"),
        ("case_at", "OpenCase", "Hotel", "iq_open_case", "case_id", "hotel_id")]


def ontology_parts(ws, lh, display_names=True):
    rng = random.Random(7007)
    nid = lambda d: str(rng.randint(10 ** (d - 1), 10 ** d - 1))
    parts, ent = [part("definition.json", {"_syncBump": "kyanos-1"})], {}
    for name, table, key, disp in ENTITIES:
        eid = nid(15)
        props = [{"id": nid(19), "name": c, "redefines": None, "baseTypeNamespaceType": None, "valueType": VT[t]} for c, t in SCHEMAS[table]]
        pid = {p["name"]: p["id"] for p in props}
        ent[name] = (eid, pid, table, key)
        parts.append(part(f"EntityTypes/{eid}/definition.json", {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/ontology/entityType/1.0.0/schema.json",
            "id": eid, "namespace": "usertypes", "baseEntityTypeId": None, "name": name, "entityIdParts": [pid[key]],
            "displayNamePropertyId": pid[disp] if display_names else None, "namespaceType": "Custom", "visibility": "Visible",
            "properties": props, "timeseriesProperties": [], "untypedProperties": []}))
        bid = str(uuid.UUID(int=rng.getrandbits(128)))
        parts.append(part(f"EntityTypes/{eid}/DataBindings/{bid}.json", {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/ontology/dataBinding/1.0.0/schema.json", "id": bid,
            "dataBindingConfiguration": {"dataBindingType": "NonTimeSeries",
                                         "propertyBindings": [{"sourceColumnName": c, "targetPropertyId": pid[c]} for c, _ in SCHEMAS[table]],
                                         "sourceTableProperties": {"sourceType": "LakehouseTable", "workspaceId": ws, "itemId": lh,
                                                                   "sourceTableName": table, "sourceSchema": "gold"}}}))
    for rname, s, t, table, skey, fk in RELS:
        rid = nid(19)
        parts.append(part(f"RelationshipTypes/{rid}/definition.json", {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/ontology/relationshipType/1.0.0/schema.json",
            "namespace": "usertypes", "id": rid, "name": rname, "namespaceType": "Custom", "source": {"entityTypeId": ent[s][0]}, "target": {"entityTypeId": ent[t][0]}}))
        cid = str(uuid.UUID(int=rng.getrandbits(128)))
        parts.append(part(f"RelationshipTypes/{rid}/Contextualizations/{cid}.json", {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/ontology/contextualization/1.0.0/schema.json", "id": cid,
            "dataBindingTable": {"workspaceId": ws, "itemId": lh, "sourceTableName": table, "sourceSchema": "gold", "sourceType": "LakehouseTable"},
            "sourceKeyRefBindings": [{"sourceColumnName": skey, "targetPropertyId": ent[s][1][skey]}],
            "targetKeyRefBindings": [{"sourceColumnName": fk, "targetPropertyId": ent[t][1][ent[t][3]]}]}))
    return parts
