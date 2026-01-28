# @get("/students", status_code=HTTP_200_OK, summary="List children")
# async def list_children(self, request: Request, db: AsyncSession) -> list[ChildOut]:
#     """List children belonging to the current caregiver."""
#     caregiver = await get_current_caregiver(request, db)
#     assert caregiver is not None  # Required by dependency
#     result = await db.execute(
#         select(Child).where(Child.caregiver_id == caregiver.id)
#     )
#     children = result.scalars().all()
#     return [
#         ChildOut(
#             id=str(c.id),
#             name=c.name,
#             dateOfBirth=c.date_of_birth,
#             mediaConsent=c.media_consent,
#             medicalInfo=c.medical_info,
#             needsDevices=c.needs_devices,
#             otherInfo=c.other_info,
#             region=c.region,
#             ethnicity=c.ethnicity,
#             schoolName=c.school_name,
#         )
#         for c in children
#     ]


# @post("/students", status_code=HTTP_200_OK, summary="Create child")
# async def create_child(
#     self, request: Request, db: AsyncSession, data: ChildCreate
# ) -> ChildOut:
#     """Create a new child record for the current caregiver."""
#     caregiver = await get_current_caregiver(request, db)
#     assert caregiver is not None  # Required by dependency
#     if not caregiver.name or not caregiver.phone:
#         raise ValidationException(
#             detail="Complete caregiver profile before adding children"
#         )

#     child = Child(
#         caregiver_id=caregiver.id,
#         name=data.name,
#         date_of_birth=data.date_of_birth,
#         media_consent=data.media_consent,
#         medical_info=data.medical_info,
#         needs_devices=data.needs_devices,
#         other_info=data.other_info,
#         region=data.region,
#         ethnicity=data.ethnicity,
#         school_name=data.school_name,
#     )
#     db.add(child)
#     await db.flush()
#     return ChildOut(
#         id=str(child.id),
#         name=child.name,
#         dateOfBirth=child.date_of_birth,
#         mediaConsent=child.media_consent,
#         medicalInfo=child.medical_info,
#         needsDevices=child.needs_devices,
#         otherInfo=child.other_info,
#         region=child.region,
#         ethnicity=child.ethnicity,
#         schoolName=child.school_name,
#     )

# @patch("/students/{child_id:uuid}", status_code=HTTP_200_OK, summary="Update child")
# async def update_child(
#     self, request: Request, db: AsyncSession, child_id: uuid.UUID, data: ChildUpdate
# ) -> ChildOut:
#     """Update an existing child record (owned by the current caregiver)."""
#     caregiver = await get_current_caregiver(request, db)
#     assert caregiver is not None  # Required by dependency
#     child = await db.get(Child, child_id)
#     if not child or child.caregiver_id != caregiver.id:
#         raise NotFoundException(detail="Child not found")

#     if data.name is not None:
#         child.name = data.name
#     if data.date_of_birth is not None:
#         child.date_of_birth = data.date_of_birth
#     if data.media_consent is not None:
#         child.media_consent = data.media_consent
#     if data.medical_info is not None:
#         child.medical_info = data.medical_info
#     if data.other_info is not None:
#         child.other_info = data.other_info
#     if data.region is not None:
#         child.region = data.region
#     if data.ethnicity is not None:
#         child.ethnicity = data.ethnicity
#     if data.school_name is not None:
#         child.school_name = data.school_name
#     await db.flush()

#     return ChildOut(
#         id=str(child.id),
#         name=child.name,
#         dateOfBirth=child.date_of_birth,
#         mediaConsent=child.media_consent,
#         medicalInfo=child.medical_info,
#         needsDevices=child.needs_devices,
#         otherInfo=child.other_info,
#         region=child.region,
#         ethnicity=child.ethnicity,
#         schoolName=child.school_name,
#     )
