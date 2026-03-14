def parse_inventory_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError("JSON object required")

    item_name = (payload.get("itemName") or "").strip()
    if not item_name:
        raise ValueError("Item name required")
#check None so quantity=0 is treated as valid
    qty_raw = payload.get("quantity")
    if qty_raw is None:
        raise ValueError("Quantity is required")
    try:
        quantity = int(str(qty_raw).strip())
    except (TypeError, ValueError):
        raise ValueError("Quantity must be an integer")

    restock_raw = payload.get("restockmin")
    if restock_raw is None or str(restock_raw).strip() == "":
        restockmin = None
    else:
        try:
            restockmin = int(str(restock_raw).strip())
        except (TypeError, ValueError):
            raise ValueError("Restock min must be an integer")

    description = (payload.get("description") or "").strip()

    return {
        "itemName": item_name,
        "quantity": quantity,
        "restockmin": restockmin,
        "description": description
    }