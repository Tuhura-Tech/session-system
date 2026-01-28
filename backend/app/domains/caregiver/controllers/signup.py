# @get("/signups", status_code=HTTP_200_OK, summary="List signups")
# async def list_signups(
#     self, request: Request, db: AsyncSession
# ) -> list[CaregiverSignupOut]:
#     """List signups for the current caregiver."""
#     caregiver = await get_current_caregiver(request, db)
#     assert caregiver is not None  # Required by dependency

#     result = await db.execute(
#         select(Signup, Session, Child)
#         .join(Session, Signup.session_id == Session.id)
#         .join(Child, Signup.child_id == Child.id)
#         .where(Signup.caregiver_id == caregiver.id)
#         .order_by(Signup.created_at.desc())
#     )

#     rows = result.all()
#     out: list[CaregiverSignupOut] = []
#     for signup, session, child in rows:
#         out.append(
#             CaregiverSignupOut(
#                 id=str(signup.id),
#                 status=signup.status,
#                 createdAt=signup.created_at,
#                 sessionId=str(session.id),
#                 sessionName=session.name,
#                 childId=str(child.id),
#                 childName=child.name,
#             )
#         )
#     return out

# @post(
#     "/signup/{signup_id:uuid}/withdraw",
#     status_code=HTTP_200_OK,
#     summary="Withdraw signup",
# )
# async def withdraw_signup(
#     self, request: Request, db: AsyncSession, signup_id: uuid.UUID
# ) -> SignupCreateResponse:
#     """Withdraw an existing signup belonging to the current caregiver."""
#     caregiver = await get_current_caregiver(request, db)
#     assert caregiver is not None  # Required by dependency
#     signup = await db.get(Signup, signup_id)
#     if not signup or signup.caregiver_id != caregiver.id:
#         raise NotFoundException(detail="Signup not found")

#     if signup.status != "withdrawn":
#         signup.status = "withdrawn"
#         signup.withdrawn_at = datetime.now(UTC)
#         await db.flush()

#     return SignupCreateResponse(
#         id=str(signup.id),
#         status=cast(
#             "Literal['pending', 'confirmed', 'waitlisted', 'withdrawn']",
#             signup.status,
#         ),
#     )

# @get(
#     "/signup/{signup_id:uuid}/calendar-feed.ics",
#     status_code=HTTP_200_OK,
#     summary="Subscribe to signup calendar",
# )
# async def get_signup_calendar_feed(
#     self, request: Request, db: AsyncSession, signup_id: uuid.UUID
# ) -> Response:
#     """Generate a subscribable calendar feed for a specific signup.

#     This provides a calendar subscription that includes all session occurrences
#     for the child's signup. The calendar automatically updates when sessions
#     are modified or cancelled.

#     Add this URL to your calendar app to keep your schedule synchronized.
#     """
#     caregiver = await get_current_caregiver(request, db)
#     assert caregiver is not None

#     # Get signup with related data
#     result = await db.execute(
#         select(Signup)
#         .options(
#             selectinload(Signup.session).selectinload(Session.session_location),
#             selectinload(Signup.session).selectinload(Session.occurrences),
#             selectinload(Signup.child),
#         )
#         .where(Signup.id == signup_id)
#         .where(Signup.caregiver_id == caregiver.id)
#     )
#     signup = result.scalar_one_or_none()

#     if not signup or signup.status == "withdrawn":
#         raise NotFoundException(detail="Signup not found or withdrawn")

#     session = signup.session
#     child = signup.child

#     # Default to Pacific/Auckland timezone
#     tzid = "Pacific/Auckland"
#     try:
#         from zoneinfo import ZoneInfo

#         tz = ZoneInfo(tzid)
#     except Exception:
#         tz = UTC
#         tzid = "UTC"

#     # Get relevant occurrences (future and recent past)
#     from datetime import timedelta

#     now = datetime.now(tz)
#     cutoff = now - timedelta(days=7)

#     occs = getattr(session, "occurrences", None) or []
#     relevant_occs = [o for o in occs if o.starts_at >= cutoff]
#     relevant_occs.sort(key=lambda o: o.starts_at)

#     # Convert to calendar feed format
#     occurrence_data = [
#         (
#             o.starts_at.astimezone(tz) if tz else o.starts_at,
#             o.ends_at.astimezone(tz) if tz else o.ends_at,
#             getattr(o, "cancelled", False),
#             getattr(o, "cancellation_reason", None),
#         )
#         for o in relevant_occs
#     ]

#     venue = (
#         session.session_location.name if session.session_location else session.name
#     )
#     address = session.session_location.address if session.session_location else ""
#     location = f"{venue} - {address}" if address else venue

#     # Include child name in session title
#     session_name = f"{session.name} - {child.name}"
#     url = f"{settings.frontend_base_url}/dashboard"

#     ics_text = build_session_calendar_feed(
#         session_id=str(signup.id),  # Use signup ID for uniqueness
#         session_name=session_name,
#         occurrences=occurrence_data,
#         location=location,
#         address=address,
#         tzid=tzid,
#         url=url,
#         refresh_interval_hours=24,
#     )

#     return Response(
#         content=ics_text,
#         media_type="text/calendar; charset=utf-8",
#         headers={
#             "Content-Disposition": f'inline; filename="session-{child.name.replace(" ", "-")}.ics"',
#             "Cache-Control": "public, max-age=3600",
#         },
#     )


# @post(
#     "/signup/{session_id:uuid}",
#     status_code=HTTP_200_OK,
#     summary="Create signup",
# )
# async def create_signup(
#     self,
#     request: Request,
#     db: AsyncSession,
#     session_id: uuid.UUID,
#     data: AuthenticatedSignupCreate,
# ) -> SignupCreateResponse:
#     """Create a signup for the caregiver's child, preventing duplicates and returning confirmed or waitlisted status with notifications queued."""
#     caregiver = await get_current_caregiver(request, db)
#     assert caregiver is not None  # Required by dependency
#     if not caregiver.name or not caregiver.phone:
#         raise ValidationException(
#             detail="Complete caregiver profile before signing up"
#         )

#     session_result = await db.execute(
#         select(Session)
#         .options(selectinload(Session.session_location))
#         .where(Session.id == session_id)
#     )
#     session = session_result.scalar_one_or_none()
#     if not session:
#         raise NotFoundException(detail="Session not found")

#     # Validate child ownership.
#     try:
#         child_uuid = uuid.UUID(data.child_id)
#     except Exception:
#         raise ValidationException(detail="Invalid childId")

#     child = await db.get(Child, child_uuid)
#     if not child or child.caregiver_id != caregiver.id:
#         raise NotFoundException(detail="Child not found")

#     if not child.date_of_birth:
#         raise ValidationException(detail="Child date of birth is required")

#     # Check if child meets age requirements
#     from datetime import date as date_type

#     today = date_type.today()
#     age = (today - child.date_of_birth).days // 365  # Rough age calculation

#     is_age_eligible = True
#     if session.age_lower is not None and age < session.age_lower:
#         is_age_eligible = False
#     if session.age_upper is not None and age > session.age_upper:
#         is_age_eligible = False

#     # Prevent duplicate signup for same child+session.
#     existing_result = await db.execute(
#         select(Signup).where(
#             Signup.session_id == session_id, Signup.child_id == child.id
#         )
#     )
#     existing = existing_result.scalar_one_or_none()
#     if existing and existing.status == "withdrawn":
#         # Re-activate a withdrawn signup (uniqueness constraint prevents creating a new row).
#         # If child is not age-eligible or session is in waitlist mode or at capacity, set to waitlisted
#         if not is_age_eligible or session.waitlist or session.is_at_capacity():
#             existing.status = "waitlisted"
#         else:
#             existing.status = "confirmed"
#         existing.withdrawn_at = None
#         existing.pickup_dropoff = data.pickup_dropoff
#         await db.flush()

#         queue = get_queue()

#         await queue.enqueue(
#             "send_signup_confirmation_task",
#             to_email=caregiver.email,
#             caregiver_name=caregiver.name,
#             child_name=child.name,
#             session_name=session.name,
#             session_venue=getattr(
#                 getattr(session, "session_location", None), "name", None
#             ),
#             session_address=getattr(
#                 getattr(session, "session_location", None), "address", None
#             ),
#             session_time=_format_time_range(
#                 session.day_of_week, session.start_time, session.end_time
#             ),
#             term_summary=f"{getattr(session, 'year', '')}"
#             if getattr(session, "session_type", "term") == "term"
#             else None,
#             what_to_bring=session.what_to_bring,
#             signup_status=existing.status,
#             signup_id=str(existing.id),
#             session_id=str(session.id),
#         )

#         return SignupCreateResponse(
#             id=str(existing.id),
#             status=cast(
#                 "Literal['pending', 'confirmed', 'waitlisted', 'withdrawn']",
#                 existing.status,
#             ),
#         )

#     # Determine status - if not age-eligible, always waitlist regardless of capacity
#     if not is_age_eligible or session.waitlist or session.is_at_capacity():
#         status = "waitlisted"
#     else:
#         status = "confirmed"

#     signup = Signup(
#         session_id=session_id,
#         caregiver_id=caregiver.id,
#         child_id=child.id,
#         status=status,
#         pickup_dropoff=data.pickup_dropoff,
#     )
#     db.add(signup)
#     await db.flush()

#     # Queue confirmation email.
#     queue = get_queue()

#     await queue.enqueue(
#         "send_signup_confirmation_task",
#         to_email=caregiver.email,
#         caregiver_name=caregiver.name,
#         child_name=child.name,
#         session_name=session.name,
#         session_venue=getattr(
#             getattr(session, "session_location", None), "name", None
#         ),
#         session_address=getattr(
#             getattr(session, "session_location", None), "address", None
#         ),
#         session_time=_format_time_range(
#             session.day_of_week, session.start_time, session.end_time
#         ),
#         term_summary=f"{getattr(session, 'year', '')}"
#         if getattr(session, "session_type", "term") == "term"
#         else None,
#         what_to_bring=session.what_to_bring,
#         signup_status=status,
#         signup_id=str(signup.id),
#         session_id=str(session.id),
#     )
#     logger.info("Queued confirmation email for signup %s", signup.id)

#     return SignupCreateResponse(id=str(signup.id), status=status)
