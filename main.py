from pydantic import BaseModel, Field, field_validator
from typing import Optional
from fastapi import FastAPI, HTTPException

app = FastAPI(
    title="QuickSwift Logistics API",
    description="Parcel pickup, tracking and delivery management API",
)

status_data: list[str] = [
    "Booked",
    "Picked Up",
    "In Transit",
    "Out for Delivery",
    "Delivered",
    "Cancelled",
]


class Address(BaseModel):
    state: str = Field(
        min_length=3, max_length=20, description="Enter State", examples=["Jharkhand"]
    )
    city: str = Field(
        min_length=3, max_length=20, description="Enter city", examples=["Jamshedpur"]
    )
    pin_code: int = Field(description="Enter PinCode", examples=[831001])

    @field_validator("pin_code")
    @classmethod
    def check_pin_code(cls, value):
        if len(str(value)) != 6:
            raise ValueError("Invalid pin code")
        return value

    @field_validator("state")
    @classmethod
    def is_digit_in_state(cls, value):
        value = value.strip()
        if any(ch.isdigit() for ch in value):
            raise ValueError("Enter valid State.")
        return value

    @field_validator("city")
    @classmethod
    def is_digit_in_city(cls, value):
        value = value.strip()
        if any(ch.isdigit() for ch in value):
            raise ValueError("Enter valid City.")
        return value


class Parcel_details(BaseModel):
    tracking_id: int = Field(gt=0, description="Enter tracking id", examples=[26209])
    sender_name: str = Field(
        min_length=3,
        max_length=20,
        description="Enter SenderName",
        examples=["Subrato Moral"],
    )
    receiver_name: str = Field(
        min_length=3,
        max_length=20,
        description="Enter ReceiverName",
        examples=["Subrato Moral"],
    )
    parcel_weight: int = Field(
        gt=0, le=50, description="Enter ParcelWeight", examples=[4]
    )
    status: str = Field(
        min_length=3,
        max_length=20,
        description="Enter Status",
        examples=[
            "Booked , Picked Up , In Transit , Out for Delivery , Delivered , Cancelled"
        ],
    )
    pickup_address: Address
    delivery_address: Address

    @field_validator("tracking_id")
    @classmethod
    def check_tracking_id(cls, value):
        if len(str(value)) != 6:
            raise ValueError(
                "Invalid tracking code tracking code contain last 2 digit of year month and product code"
            )
        return value

    @field_validator("sender_name")
    @classmethod
    def check_sender_name(cls, value):
        value = value.strip()
        if any(ch.isdigit() for ch in value):
            raise ValueError("Sender name doesn't contain digits")
        return value

    @field_validator("receiver_name")
    @classmethod
    def check_receiver_name(cls, value):
        value = value.strip()
        if any(ch.isdigit() for ch in value):
            raise ValueError("Receiver name doesn't contain digits")
        return value

    @field_validator("status")
    @classmethod
    def check_status(cls, value):
        st: bool = False
        for val in status_data:
            if value.strip().lower() == val.strip().lower():
                st = True
                break
        if st:
            return value
        raise ValueError("error : wrong status detail input")


class UpdateParcel_details(BaseModel):
    receiver_name: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=20,
        description="Enter ReceiverName",
    )
    parcel_weight: Optional[int] = Field(
        default=None, gt=0, le=50, description="Enter ParcelWeight"
    )
    status: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=20,
        description="Enter Status",
        examples=[
            "Booked , Picked Up , In Transit , Out for Delivery , Delivered , Cancelled"
        ],
    )

    delivery_address: Optional[Address] = None

    @field_validator("receiver_name")
    @classmethod
    def check_receiver_name(cls, value):
        value = value.strip()
        if any(ch.isdigit() for ch in value):
            raise ValueError("Receiver name doesn't contain digits")
        return value

    @field_validator("status")
    @classmethod
    def check_status(cls, value):
        st: bool = False
        if value is None:
            raise ValueError("Status cannot be null")
        for val in status_data:
            if value.strip().lower() == val.strip().lower():
                st = True
                break
        if st:
            return value
        raise ValueError("error : wrong status detail input")


parcels: list[Parcel_details] = []


@app.post("/QuickSwift/upload", response_model=Parcel_details, tags=["QuickSwift"])
def upload_data(qc_parcel: Parcel_details):
    if qc_parcel.delivery_address == qc_parcel.pickup_address:
        raise HTTPException(
            status_code=400, detail="Delivery Address and Pickup Address can't be same"
        )
    for id in parcels:
        if qc_parcel.tracking_id == id.tracking_id:
            raise HTTPException(status_code=409, detail="duplicate tracking id")
    parcels.append(qc_parcel)
    return qc_parcel


@app.get("/QuickSwift/get", response_model=list[Parcel_details], tags=["QuickSwift"])
def get_parcel_data():
    return parcels


@app.get(
    "/QuickSwift/get/{tracking_id}", response_model=Parcel_details, tags=["QuickSwift"]
)
def get_by_tracking(tracking_id: int):
    for id in parcels:
        if id.tracking_id == tracking_id:
            return id
    raise HTTPException(status_code=404, detail="data not found!")


@app.get(
    "/QuickSwift/get/parcels/status/{parcel_status}",
    response_model=list[Parcel_details],
    tags=["QuickSwift"],
)
def check_by_status(parcel_status: str):
    status_store: list[Parcel_details] = []
    for sta in parcels:
        if sta.status.strip().lower() == parcel_status.strip().lower():
            status_store.append(sta)
    if not status_store:
        raise HTTPException(status_code=404, detail="data not found")
    return status_store


@app.patch(
    "/QuickSwift/update_details/{track_id}",
    response_model=Parcel_details,
    tags=["QuickSwift"],
)
def update_details(track_id: int, update: UpdateParcel_details):
    for data in parcels:
        if data.tracking_id == track_id:
            if update.receiver_name is not None:
                data.receiver_name = update.receiver_name
            if update.parcel_weight is not None:
                data.parcel_weight = update.parcel_weight
            if update.status is not None:
                if data.status == update.status:
                    raise HTTPException(
                        status_code=400, detail="same data can't be updated"
                    )
                checkstatusdetails(data.status, update.status)
                data.status = update.status
            if update.delivery_address is not None:
                data.delivery_address = update.delivery_address
            return data
    else:
        raise HTTPException(status_code=404, detail="data not found!")


@app.delete("/QuickSwift/delete.parcel/{track_id}", tags=["QuickSwift"])
def delete_parcel(track_id: int):
    for data in parcels:
        if data.tracking_id == track_id:
            parcels.remove(data)
            return {"status": "parcel data deleted successfully"}
    raise HTTPException(status_code=404, detail="data not found")


def checkstatusdetails(data: str, update: str):
    data = data.strip().lower()
    update = update.strip().lower()
    if data == "booked":
        if update == "delivered":
            raise HTTPException(
                status_code=400,
                detail="error : some internal issue resolved as possible",
            )
        elif update == "out for delivery":
            raise HTTPException(
                status_code=400,
                detail="error : some internal issue resolved as possible",
            )
        elif update == "in transit":
            raise HTTPException(
                status_code=400,
                detail="error : some internal issue resolved as possible",
            )

    elif data == "delivered":
        if update == "in transit":
            raise HTTPException(
                status_code=400,
                detail="error : some internal issue resolved as possible",
            )
        elif update == "picked up":
            raise HTTPException(
                status_code=400,
                detail="error : some internal issue resolved as possible",
            )
        elif update == "booked":
            raise HTTPException(
                status_code=400,
                detail="error : some internal issue resolved as possible",
            )
        elif update == "out for delivery":
            raise HTTPException(
                status_code=400,
                detail="error : some internal issue resolved as possible",
            )
        elif update == "cancelled":
            raise HTTPException(
                status_code=400,
                detail="error : some internal issue resolved as possible",
            )
    elif data == "picked up":
        if update == "delivered":
            raise HTTPException(
                status_code=400,
                detail="error : some internal issue resolved as possible",
            )
        elif update == "booked":
            raise HTTPException(
                status_code=400,
                detail="error : some internal issue resolved as possible",
            )
        elif update == "out for delivery":
            raise HTTPException(
                status_code=400,
                detail="error : some internal issue resolved as possible",
            )
    elif data == "in transit":
        if update == "delivered":
            raise HTTPException(
                status_code=400,
                detail="error : some internal issue resolved as possible",
            )
        elif update == "booked":
            raise HTTPException(
                status_code=400,
                detail="error : some internal issue resolved as possible",
            )
        elif update == "picked up":
            raise HTTPException(
                status_code=400,
                detail="error : some internal issue resolved as possible",
            )
    elif data == "cancelled":
        if update == "delivered":
            raise HTTPException(
                status_code=400,
                detail="error : some internal issue resolved as possible",
            )
        elif update == "out for delivery":
            raise HTTPException(
                status_code=400,
                detail="error : some internal issue resolved as possible",
            )
        elif update == "picked up":
            raise HTTPException(
                status_code=400,
                detail="error : some internal issue resolved as possible",
            )
        elif update == "in transit":
            raise HTTPException(
                status_code=400,
                detail="error : some internal issue resolved as possible",
            )
        elif update == "booked":
            raise HTTPException(
                status_code=400,
                detail="error : some internal issue resolved as possible",
            )
    elif data == "out for delivery":
        if update == "picked up":
            raise HTTPException(
                status_code=400,
                detail="error : some internal issue resolved as possible",
            )
        elif update == "in transit":
            raise HTTPException(
                status_code=400,
                detail="error : some internal issue resolved as possible",
            )
        elif update == "booked":
            raise HTTPException(
                status_code=400,
                detail="error : some internal issue resolved as possible",
            )
