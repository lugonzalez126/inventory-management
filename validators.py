def parse_inventory_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError("JSON object required")

    item_name = (payload.get("itemName") or "").strip()
    if not item_name:
        raise ValueError("Item name required")

    qty_raw = (payload.get("quantity") or "").strip()
    try:
        quantity = int(qty_raw)
    except (TypeError, ValueError):
        raise ValueError("Quantity must be an integer")
    if quantity < 0:
        raise ValueError("Quantity must be >= 0")

    restock_raw = (payload.get("restockmin") or "").strip()
    if restock_raw == "":
        restockmin = None
    else:
        try:
            restockmin = int(restock_raw)
        except (TypeError, ValueError):
            raise ValueError("Restock min must be an integer")

    description = (payload.get("description") or "").strip()

    return {
        "itemName": item_name,
        "quantity": quantity,
        "restockmin": restockmin,
        "description": description
    }