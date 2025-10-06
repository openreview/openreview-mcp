"""Utility module for introspecting the openreview-py library structure."""

import inspect
import importlib
from typing import Dict, List, Any, Optional


def get_openreview_functions() -> List[Dict[str, Any]]:
    """
    Extract function metadata from the openreview-py library.
    
    Returns a list of dictionaries containing function information:
    - name: Function name
    - docstring: Function docstring
    - module: Module path
    - signature: Function signature as string
    """
    # Extract functions from the OpenReviewClient class methods
    functions = [
        {
            "name": "get_note",
            "docstring": "Get a single Note by id if available",
            "module": "openreview.api.OpenReviewClient",
            "signature": "get_note(id, details=None)",
            "function_type": "method",
            "return_type": "openreview.api.Note"
        },
        {
            "name": "get_notes",
            "docstring": "Gets list of Note objects based on the filters provided. The Notes that will be returned match all the criteria passed in the parameters.",
            "module": "openreview.api.OpenReviewClient",
            "signature": "get_notes(id=None, paperhash=None, forum=None, invitation=None, parent_invitations=None, replyto=None, tauthor=None, signature=None, transitive_members=None, signatures=None, writer=None, trash=None, number=None, content=None, limit=None, offset=None, after=None, mintcdate=None, domain=None, details=None, sort=None, with_count=None, stream=None)",
            "function_type": "method",
            "return_type": "List[openreview.api.Note]"
        },
        {
            "name": "post_note_edit",
            "docstring": "Posts a note edit",
            "module": "openreview.api.OpenReviewClient",
            "signature": "post_note_edit(invitation, signatures, note=None, readers=None, writers=None, nonreaders=None, content=None, await_process=False)",
            "function_type": "method",
            "return_type": "Dict"
        },
        {
            "name": "get_group",
            "docstring": "Get a single Group by id if available",
            "module": "openreview.api.OpenReviewClient",
            "signature": "get_group(id, details=None)",
            "function_type": "method",
            "return_type": "openreview.api.Group"
        },
        {
            "name": "get_invitation",
            "docstring": "Get a single invitation by id if available",
            "module": "openreview.api.OpenReviewClient",
            "signature": "get_invitation(id)",
            "function_type": "method",
            "return_type": "openreview.api.Invitation"
        },
        {
            "name": "search_notes",
            "docstring": "Searches notes based on term, content, group and source as the criteria. Unlike get_notes, this method uses Elasticsearch to retrieve the Notes",
            "module": "openreview.api.OpenReviewClient",
            "signature": "search_notes(term, content='all', group='all', source='all', limit=None, offset=None)",
            "function_type": "method",
            "return_type": "List[openreview.api.Note]"
        },
        {
            "name": "get_profile",
            "docstring": "Get a single Profile by id, if available",
            "module": "openreview.api.OpenReviewClient",
            "signature": "get_profile(email_or_id=None)",
            "function_type": "method",
            "return_type": "Dict"
        },
        {
            "name": "post_message",
            "docstring": "Posts a message to the recipients and consequently sends them emails",
            "module": "openreview.api.OpenReviewClient",
            "signature": "post_message(subject, recipients, message, invitation=None, signature=None, ignoreRecipients=None, sender=None, replyTo=None, parentGroup=None, use_job=None)",
            "function_type": "method",
            "return_type": "Dict"
        },
        {
            "name": "login_user",
            "docstring": "Logs in a registered user",
            "module": "openreview.api.OpenReviewClient",
            "signature": "login_user(username=None, password=None, expiresIn=None)",
            "function_type": "method",
            "return_type": "Dict"
        },
        {
            "name": "register_user",
            "docstring": "Registers a new user",
            "module": "openreview.api.OpenReviewClient",
            "signature": "register_user(email=None, fullname=None, password=None)",
            "function_type": "method",
            "return_type": "Dict"
        }
    ]
    
    return functions


def get_openreview_classes() -> List[Dict[str, Any]]:
    """
    Extract class metadata from the openreview-py library.
    
    Returns a list of dictionaries containing class information:
    - name: Class name
    - docstring: Class docstring
    - module: Module path
    - methods: List of public methods with their signatures
    """
    # Classes from client.py
    classes = [
        {
            "name": "OpenReviewClient",
            "docstring": """OpenReviewClient for API interactions.
            
            :param baseurl: URL to the host, example: https://api2.openreview.net (should be replaced by 'host' name). If none is provided, it defaults to the environment variable `OPENREVIEW_API_BASEURL_V2`
            :type baseurl: str, optional
            :param username: OpenReview username. If none is provided, it defaults to the environment variable `OPENREVIEW_USERNAME`
            :type username: str, optional
            :param password: OpenReview password. If none is provided, it defaults to the environment variable `OPENREVIEW_PASSWORD`
            :type password: str, optional
            :param token: Session token. This token can be provided instead of the username and password if the user had already logged in
            :type token: str, optional
            :param expiresIn: Time in seconds before the token expires. If none is set the value will be set automatically to one hour. The max value that it can be set to is 1 week.
            :type expiresIn: number, optional
            """,
            "module": "openreview.api",
            "methods": [
                # Authentication Methods
                {
                    "name": "__init__",
                    "signature": "__init__(baseurl=None, username=None, password=None, token=None, tokenExpiresIn=None)",
                    "docstring": "Initialize the OpenReview client"
                },
                {
                    "name": "login_user",
                    "signature": "login_user(username=None, password=None, expiresIn=None)",
                    "docstring": "Logs in a registered user"
                },
                {
                    "name": "register_user",
                    "signature": "register_user(email=None, fullname=None, password=None)",
                    "docstring": "Registers a new user"
                },
                {
                    "name": "activate_user",
                    "signature": "activate_user(token, content)",
                    "docstring": "Activates a newly registered user"
                },
                {
                    "name": "impersonate",
                    "signature": "impersonate(group_id)",
                    "docstring": "Impersonate a group"
                },
                {
                    "name": "confirm_alternate_email",
                    "signature": "confirm_alternate_email(profile_id, alternate_email, activation_token=None)",
                    "docstring": "Confirms an alternate email address"
                },
                {
                    "name": "activate_email_with_token",
                    "signature": "activate_email_with_token(email, token, activation_token=None)",
                    "docstring": "Activates an email address"
                },
                {
                    "name": "get_activatable",
                    "signature": "get_activatable(token=None)",
                    "docstring": "Get activatable user with token"
                },
                
                # Group Methods
                {
                    "name": "get_group",
                    "signature": "get_group(id, details=None)",
                    "docstring": "Get a single Group by id if available"
                },
                {
                    "name": "get_groups",
                    "signature": "get_groups(id=None, prefix=None, member=None, members=None, signatory=None, web=None, limit=None, offset=None, after=None, stream=None, sort=None, with_count=None)",
                    "docstring": "Gets list of Group objects based on the filters provided. The Groups that will be returned match all the criteria passed in the parameters."
                },
                {
                    "name": "get_all_groups",
                    "signature": "get_all_groups(id=None, parent=None, prefix=None, member=None, members=None, domain=None, signatory=None, web=None, sort=None, with_count=None)",
                    "docstring": "Gets list of Group objects based on the filters provided. The Groups that will be returned match all the criteria passed in the parameters."
                },
                {
                    "name": "post_group_edit",
                    "signature": "post_group_edit(invitation, signatures=None, group=None, readers=None, writers=None, content=None, replacement=None, await_process=False, flush_members_cache=True)",
                    "docstring": "Posts a group edit"
                },
                {
                    "name": "get_group_edit",
                    "signature": "get_group_edit(id)",
                    "docstring": "Get a single group edit by id if available"
                },
                {
                    "name": "get_group_edits",
                    "signature": "get_group_edits(group_id=None, invitation=None, with_count=False, sort=None, trash=None)",
                    "docstring": "Gets a list of edits for a group. The edits that will be returned match all the criteria passed in the parameters."
                },
                {
                    "name": "add_members_to_group",
                    "signature": "add_members_to_group(group, members)",
                    "docstring": "Adds members to a group"
                },
                {
                    "name": "remove_members_from_group",
                    "signature": "remove_members_from_group(group, members)",
                    "docstring": "Removes members from a group"
                },
                {
                    "name": "delete_group",
                    "signature": "delete_group(group_id)",
                    "docstring": "Deletes the group"
                },
                {
                    "name": "flush_members_cache",
                    "signature": "flush_members_cache(group_id=None)",
                    "docstring": "Flushes the members cache for a group"
                },
                
                # Invitation Methods
                {
                    "name": "get_invitation",
                    "signature": "get_invitation(id)",
                    "docstring": "Get a single invitation by id if available"
                },
                {
                    "name": "get_invitations",
                    "signature": "get_invitations(id=None, ids=None, invitee=None, replytoNote=None, replyForum=None, signature=None, note=None, prefix=None, tags=None, limit=None, offset=None, after=None, minduedate=None, duedate=None, pastdue=None, replyto=None, details=None, expired=None, sort=None, type=None, with_count=None, invitation=None, trash=None)",
                    "docstring": "Gets list of Invitation objects based on the filters provided. The Invitations that will be returned match all the criteria passed in the parameters."
                },
                {
                    "name": "get_all_invitations",
                    "signature": "get_all_invitations(id=None, ids=None, invitee=None, replytoNote=None, replyForum=None, signature=None, note=None, prefix=None, tags=None, minduedate=None, duedate=None, pastdue=None, replyto=None, details=None, expired=None, sort=None, type=None, with_count=None, invitation=None, trash=None)",
                    "docstring": "Gets list of Invitation objects based on the filters provided. The Invitations that will be returned match all the criteria passed in the parameters."
                },
                {
                    "name": "post_invitation_edit",
                    "signature": "post_invitation_edit(invitations, readers=None, writers=None, signatures=None, invitation=None, content=None, replacement=None, domain=None, await_process=False)",
                    "docstring": "Posts an invitation edit"
                },
                {
                    "name": "get_invitation_edit",
                    "signature": "get_invitation_edit(id)",
                    "docstring": "Get a single invitation edit by id if available"
                },
                {
                    "name": "get_invitation_edits",
                    "signature": "get_invitation_edits(invitation_id=None, invitation=None, with_count=None, sort=None)",
                    "docstring": "Gets a list of edits for an invitation. The edits that will be returned match all the criteria passed in the parameters."
                },
                {
                    "name": "get_invitation_date_process_job",
                    "signature": "get_invitation_date_process_job(job_id)",
                    "docstring": "Get date process job for an invitation"
                },
                {
                    "name": "reschedule_date_process_jobs",
                    "signature": "reschedule_date_process_jobs(invitation_id)",
                    "docstring": "Reschedule date process jobs for an invitation"
                },
                
                # Note Methods
                {
                    "name": "get_note",
                    "signature": "get_note(id, details=None)",
                    "docstring": "Get a single Note by id if available"
                },
                {
                    "name": "get_notes",
                    "signature": "get_notes(id=None, paperhash=None, forum=None, invitation=None, parent_invitations=None, replyto=None, tauthor=None, signature=None, transitive_members=None, signatures=None, writer=None, trash=None, number=None, content=None, limit=None, offset=None, after=None, mintcdate=None, domain=None, details=None, sort=None, with_count=None, stream=None)",
                    "docstring": "Gets list of Note objects based on the filters provided. The Notes that will be returned match all the criteria passed in the parameters."
                },
                {
                    "name": "get_all_notes",
                    "signature": "get_all_notes(id=None, paperhash=None, forum=None, invitation=None, replyto=None, signature=None, transitive_members=None, signatures=None, writer=None, trash=None, number=None, content=None, mintcdate=None, details=None, select=None, sort=None, with_count=None)",
                    "docstring": "Gets list of Note objects based on the filters provided. The Notes that will be returned match all the criteria passed in the parameters."
                },
                {
                    "name": "post_note_edit",
                    "signature": "post_note_edit(invitation, signatures, note=None, readers=None, writers=None, nonreaders=None, content=None, await_process=False)",
                    "docstring": "Posts a note edit"
                },
                {
                    "name": "get_note_edit",
                    "signature": "get_note_edit(id, trash=None)",
                    "docstring": "Get a single note edit by id if available"
                },
                {
                    "name": "get_note_edits",
                    "signature": "get_note_edits(note_id=None, invitation=None, with_count=None, sort=None, trash=None, limit=None)",
                    "docstring": "Gets a list of edits for a note. The edits that will be returned match all the criteria passed in the parameters."
                },
                {
                    "name": "search_notes",
                    "signature": "search_notes(term, content='all', group='all', source='all', limit=None, offset=None)",
                    "docstring": "Searches notes based on term, content, group and source as the criteria. Unlike get_notes, this method uses Elasticsearch to retrieve the Notes"
                },
                {
                    "name": "get_notes_by_ids",
                    "signature": "get_notes_by_ids(ids)",
                    "docstring": "Get notes by their IDs"
                },
                {
                    "name": "delete_note",
                    "signature": "delete_note(note_id)",
                    "docstring": "Deletes the note"
                },
                
                # Tag Methods
                {
                    "name": "get_tag",
                    "signature": "get_tag(id)",
                    "docstring": "Get a single Tag by id if available"
                },
                {
                    "name": "get_tags",
                    "signature": "get_tags(id=None, invitation=None, parent_invitations=None, forum=None, profile=None, signature=None, tag=None, limit=None, offset=None, with_count=None, mintmdate=None, stream=None)",
                    "docstring": "Gets a list of Tag objects based on the filters provided. The Tags that will be returned match all the criteria passed in the parameters."
                },
                {
                    "name": "get_all_tags",
                    "signature": "get_all_tags(id=None, invitation=None, parent_invitations=None, forum=None, profile=None, signature=None, tag=None, limit=None, offset=None, with_count=None)",
                    "docstring": "Gets a list of Tag objects based on the filters provided. The Tags that will be returned match all the criteria passed in the parameters."
                },
                {
                    "name": "post_tag",
                    "signature": "post_tag(tag)",
                    "docstring": "Posts the tag."
                },
                {
                    "name": "post_tags",
                    "signature": "post_tags(tags)",
                    "docstring": "Posts the list of Tags. Returns a list Tag objects updated with their ids."
                },
                {
                    "name": "rename_tags",
                    "signature": "rename_tags(current_id, new_id)",
                    "docstring": "Updates a Tag"
                },
                {
                    "name": "delete_tags",
                    "signature": "delete_tags(invitation, id=None, label=None, wait_to_finish=False, soft_delete=False)",
                    "docstring": "Deletes tags by a combination of invitation id and one or more of the optional filters."
                },
                
                # Edge Methods
                {
                    "name": "get_edge",
                    "signature": "get_edge(id, trash=False)",
                    "docstring": "Get a single Edge by id if available"
                },
                {
                    "name": "get_edges",
                    "signature": "get_edges(id=None, invitation=None, head=None, tail=None, label=None, limit=None, offset=None, with_count=None, trash=None)",
                    "docstring": "Returns a list of Edge objects based on the filters provided."
                },
                {
                    "name": "get_all_edges",
                    "signature": "get_all_edges(id=None, invitation=None, head=None, tail=None, label=None, limit=None, offset=None, with_count=None, trash=None)",
                    "docstring": "Returns a list of Edge objects based on the filters provided."
                },
                {
                    "name": "get_edges_count",
                    "signature": "get_edges_count(id=None, invitation=None, head=None, tail=None, label=None, domain=None)",
                    "docstring": "Returns a list of Edge objects based on the filters provided."
                },
                {
                    "name": "get_grouped_edges",
                    "signature": "get_grouped_edges(invitation=None, head=None, tail=None, label=None, groupby='head', select=None, limit=None, offset=None, trash=None)",
                    "docstring": "Returns a list of JSON objects where each one represents a group of edges."
                },
                {
                    "name": "get_archived_edges",
                    "signature": "get_archived_edges(invitation)",
                    "docstring": "Returns a list of Edge objects based on the filters provided."
                },
                {
                    "name": "post_edge",
                    "signature": "post_edge(edge)",
                    "docstring": "Posts the edge. Upon success, returns the posted Edge object."
                },
                {
                    "name": "post_edges",
                    "signature": "post_edges(edges)",
                    "docstring": "Posts the list of Edges. Returns a list Edge objects updated with their ids."
                },
                {
                    "name": "rename_edges",
                    "signature": "rename_edges(current_id, new_id)",
                    "docstring": "Updates an Edge"
                },
                {
                    "name": "delete_edges",
                    "signature": "delete_edges(invitation, id=None, label=None, head=None, tail=None, wait_to_finish=False, soft_delete=False)",
                    "docstring": "Deletes edges by a combination of invitation id and one or more of the optional filters."
                },
                
                # Profile Methods
                {
                    "name": "get_profile",
                    "signature": "get_profile(email_or_id=None)",
                    "docstring": "Get a single Profile by id, if available"
                },
                {
                    "name": "get_profiles",
                    "signature": "get_profiles(id=None, trash=None, with_blocked=None, offset=None, limit=None, sort=None)",
                    "docstring": "Get a list of Profiles"
                },
                {
                    "name": "search_profiles",
                    "signature": "search_profiles(confirmedEmails=None, emails=None, ids=None, term=None, first=None, middle=None, last=None, fullname=None, relation=None, use_ES=False)",
                    "docstring": "Gets a list of profiles using either their ids or corresponding emails"
                },
                {
                    "name": "post_profile",
                    "signature": "post_profile(profile)",
                    "docstring": "Updates a Profile"
                },
                {
                    "name": "rename_profile",
                    "signature": "rename_profile(current_id, new_id)",
                    "docstring": "Updates a the profile id of a Profile"
                },
                {
                    "name": "merge_profiles",
                    "signature": "merge_profiles(profileTo, profileFrom)",
                    "docstring": "Merges two Profiles"
                },
                {
                    "name": "moderate_profile",
                    "signature": "moderate_profile(profile_id, decision)",
                    "docstring": "Updates a Profile"
                },
                {
                    "name": "delete_profile_reference",
                    "signature": "delete_profile_reference(reference_id)",
                    "docstring": "Deletes the Profile Reference specified by reference_id."
                },
                {
                    "name": "update_relation_readers",
                    "signature": "update_relation_readers(update)",
                    "docstring": "Updates the relation readers available in the profile. This is an admin method."
                },
                
                # Message Methods
                {
                    "name": "post_message",
                    "signature": "post_message(subject, recipients, message, invitation=None, signature=None, ignoreRecipients=None, sender=None, replyTo=None, parentGroup=None, use_job=None)",
                    "docstring": "Posts a message to the recipients and consequently sends them emails"
                },
                {
                    "name": "post_message_request",
                    "signature": "post_message_request(subject, recipients, message, invitation=None, signature=None, ignoreRecipients=None, sender=None, replyTo=None, parentGroup=None, use_job=None)",
                    "docstring": "Posts a message to the recipients and consequently sends them emails"
                },
                {
                    "name": "get_message_requests",
                    "signature": "get_message_requests(id=None, invitation=None)",
                    "docstring": "Gets message requests"
                },
                {
                    "name": "post_direct_message",
                    "signature": "post_direct_message(subject, recipients, message, sender=None)",
                    "docstring": "Posts a message to the recipients and consequently sends them emails"
                },
                {
                    "name": "get_messages",
                    "signature": "get_messages(to=None, subject=None, status=None, offset=None, limit=None)",
                    "docstring": "**Only for Super User**. Retrieves all the messages sent to a list of usernames or emails and/or a particular e-mail subject"
                },
                
                # File Methods
                {
                    "name": "get_pdf",
                    "signature": "get_pdf(id, is_reference=False)",
                    "docstring": "Gets the binary content of a pdf using the provided note/reference id"
                },
                {
                    "name": "get_attachment",
                    "signature": "get_attachment(field_name, id=None, ids=None, group_id=None, invitation_id=None)",
                    "docstring": "Gets the binary content of a attachment using the provided note id"
                },
                {
                    "name": "put_attachment",
                    "signature": "put_attachment(file_path, invitation, name)",
                    "docstring": "Uploads a file to the openreview server"
                },
                
                # Venue Methods
                {
                    "name": "get_venues",
                    "signature": "get_venues(id=None, ids=None, invitations=None)",
                    "docstring": "Gets list of Note objects based on the filters provided. The Notes that will be returned match all the criteria passed in the parameters."
                },
                {
                    "name": "post_venue",
                    "signature": "post_venue(venue)",
                    "docstring": "Posts the venue. Upon success, returns the posted Venue object."
                },
                {
                    "name": "rename_venue",
                    "signature": "rename_venue(old_venue_id, new_venue_id, request_form=None, additional_renames=None)",
                    "docstring": "Updates the domain for an entire venue"
                },
                {
                    "name": "rename_domain",
                    "signature": "rename_domain(old_domain, new_domain, request_form, additional_renames=None)",
                    "docstring": "Updates the domain for an entire venue"
                },
                
                # Institution Methods
                {
                    "name": "get_institutions",
                    "signature": "get_institutions(id=None, domain=None)",
                    "docstring": "Get a single Institution by id or domain if available"
                },
                {
                    "name": "post_institution",
                    "signature": "post_institution(institution)",
                    "docstring": "Requires Super User permission. Adds an institution if the institution id is not found in the database, otherwise, the institution is updated."
                },
                {
                    "name": "delete_institution",
                    "signature": "delete_institution(institution_id)",
                    "docstring": "Deletes the institution"
                },
                
                # Utility Methods
                {
                    "name": "get_tildeusername",
                    "signature": "get_tildeusername(fullname)",
                    "docstring": "Gets next possible tilde user name corresponding to the specified full name"
                },
                {
                    "name": "get_process_logs",
                    "signature": "get_process_logs(id=None, invitation=None, status=None, min_sdate=None)",
                    "docstring": "**Only for Super User**. Retrieves the logs of the process function executed by an Invitation"
                },
                {
                    "name": "get_jobs_status",
                    "signature": "get_jobs_status()",
                    "docstring": "**Only for Super User**. Retrieves the jobs status of the queue"
                },
                {
                    "name": "post_edit",
                    "signature": "post_edit(edit)",
                    "docstring": "Posts an edit"
                },
                
                # Expertise Methods
                {
                    "name": "request_expertise",
                    "signature": "request_expertise(name, group_id, venue_id, submission_content=None, alternate_match_group=None, expertise_selection_id=None, model=None, baseurl=None, weight=None, top_recent_pubs=None)",
                    "docstring": "Request expertise computation"
                },
                {
                    "name": "request_single_paper_expertise",
                    "signature": "request_single_paper_expertise(name, group_id, paper_id, expertise_selection_id=None, model=None, baseurl=None)",
                    "docstring": "Request expertise computation for a single paper"
                },
                {
                    "name": "request_paper_similarity",
                    "signature": "request_paper_similarity(name, venue_id=None, alternate_venue_id=None, invitation=None, alternate_invitation=None, model='specter2+scincl', baseurl=None)",
                    "docstring": "Call to the Expertise API to compute paper-to-paper similarity scores. This can be between 2 different venues or between submissions of the same venue."
                },
                {
                    "name": "request_paper_subset_expertise",
                    "signature": "request_paper_subset_expertise(name, submissions, group_id, expertise_selection_id=None, model='specter2+scincl', weight=None, baseurl=None)",
                    "docstring": "Call to the Expertise API to compute scores for a subset of papers to a group."
                },
                {
                    "name": "request_user_subset_expertise",
                    "signature": "request_user_subset_expertise(name, members, expertise_selection_id=None, venue_id=None, invitation=None, model='specter2+scincl', weight=None, baseurl=None)",
                    "docstring": "Call to the Expertise API to compute scores for a subset of users to papers."
                },
                {
                    "name": "get_expertise_status",
                    "signature": "get_expertise_status(job_id=None, group_id=None, paper_id=None, baseurl=None)",
                    "docstring": "Get expertise computation status"
                },
                {
                    "name": "get_expertise_jobs",
                    "signature": "get_expertise_jobs(status=None, baseurl=None)",
                    "docstring": "Get expertise jobs"
                },
                {
                    "name": "get_expertise_results",
                    "signature": "get_expertise_results(job_id, baseurl=None, wait_for_complete=False)",
                    "docstring": "Get expertise computation results"
                }
            ]
        },
        {
            "name": "Note",
            "docstring": "Represents a note in OpenReview",
            "module": "openreview.api",
            "methods": [
                {
                    "name": "__init__",
                    "signature": "__init__(invitations=None, parent_invitations=None, readers=None, writers=None, signatures=None, content=None, id=None, number=None, cdate=None, pdate=None, odate=None, mdate=None, tcdate=None, tmdate=None, ddate=None, forum=None, replyto=None, nonreaders=None, domain=None, details=None, license=None)",
                    "docstring": "Initialize a Note object"
                },
                {
                    "name": "to_json",
                    "signature": "to_json()",
                    "docstring": "Converts Note instance to a dictionary. The instance variable names are the keys and their values the values of the dictinary."
                },
                {
                    "name": "from_json",
                    "signature": "from_json(n)",
                    "docstring": "Creates a Note object from a dictionary that contains keys values equivalent to the name of the instance variables of the Note class"
                }
            ]
        },
        {
            "name": "Invitation",
            "docstring": "Represents an invitation in OpenReview",
            "module": "openreview.api",
            "methods": [
                {
                    "name": "__init__",
                    "signature": "__init__(id=None, invitations=None, parent_invitations=None, domain=None, readers=None, writers=None, invitees=None, signatures=None, edit=None, edge=None, tag=None, message=None, type='Note', noninvitees=None, nonreaders=None, web=None, process=None, preprocess=None, date_processes=None, post_processes=None, duedate=None, expdate=None, cdate=None, ddate=None, tcdate=None, tmdate=None, minReplies=None, maxReplies=None, bulk=None, content=None, reply_forum_views=[], responseArchiveDate=None, details=None, description=None, instructions=None)",
                    "docstring": "Initialize an Invitation object"
                },
                {
                    "name": "to_json",
                    "signature": "to_json()",
                    "docstring": "Converts Invitation instance to a dictionary. The instance variable names are the keys and their values the values of the dictinary."
                },
                {
                    "name": "from_json",
                    "signature": "from_json(i)",
                    "docstring": "Creates an Invitation object from a dictionary that contains keys values equivalent to the name of the instance variables of the Invitation class"
                },
                {
                    "name": "is_active",
                    "signature": "is_active()",
                    "docstring": "Check if the invitation is currently active"
                },
                {
                    "name": "pretty_id",
                    "signature": "pretty_id()",
                    "docstring": "Returns a formatted version of the invitation ID"
                }
            ]
        },
        {
            "name": "Group",
            "docstring": """When a user is created, it is automatically assigned to certain groups that give him different privileges. A username is also a group, therefore, groups can be members of other groups.

    :param id: id of the Group
    :type id: str
    :param readers: List of readers in the Group, each reader is a Group id
    :type readers: list[str]
    :param writers: List of writers in the Group, each writer is a Group id
    :type writers: list[str]
    :param signatories: List of signatories in the Group, each writer is a Group id
    :type signatories: list[str]
    :param signatures: List of signatures in the Group, each signature is a Group id
    :type signatures: list[str]
    :param cdate: Creation date of the Group
    :type cdate: int, optional
    :param ddate: Deletion date of the Group
    :type ddate: int, optional
    :param tcdate: true creation date of the Group
    :type tcdate: int, optional
    :param tmdate: true modification date of the Group
    :type tmdate: int, optional
    :param members: List of members in the Group, each member is a Group id
    :type members: list[str], optional
    :param nonreaders: List of nonreaders in the Group, each nonreader is a Group id
    :type nonreaders: list[str], optional
    :param web: Path to a file that contains the webfield
    :type web: optional
    :param web_string: String containing the webfield for this Group
    :type web_string: str, optional
    :param details:
    :type details: optional""",
            "module": "openreview.api",
            "methods": [
                {
                    "name": "__init__",
                    "signature": "__init__(id=None, content=None, readers=None, writers=None, signatories=None, signatures=None, invitation=None, invitations=None, parent_invitations=None, cdate=None, ddate=None, tcdate=None, tmdate=None, members=None, nonreaders=None, impersonators=None, web=None, anonids=None, deanonymizers=None, host=None, domain=None, parent=None, details=None, description=None)",
                    "docstring": "Initialize a Group object"
                },
                {
                    "name": "to_json",
                    "signature": "to_json()",
                    "docstring": "Converts Group instance to a dictionary. The instance variable names are the keys and their values the values of the dictinary."
                },
                {
                    "name": "from_json",
                    "signature": "from_json(g)",
                    "docstring": "Creates a Group object from a dictionary that contains keys values equivalent to the name of the instance variables of the Group class"
                },
                {
                    "name": "add_member",
                    "signature": "add_member(member)",
                    "docstring": "Adds a member to the group. This is done only on the object not in OpenReview. Another method like :meth:`~openreview.Group.post` is needed for the change to show in OpenReview"
                },
                {
                    "name": "remove_member",
                    "signature": "remove_member(member)",
                    "docstring": "Removes a member from the group. This is done only on the object not in OpenReview. Another method like :meth:`~openreview.Group.post` is needed for the change to show in OpenReview"
                }
            ]
        },
        {
            "name": "Edge",
            "docstring": "Represents an edge between entities in OpenReview",
            "module": "openreview.api",
            "methods": [
                {
                    "name": "__init__",
                    "signature": "__init__(head, tail, invitation, domain=None, readers=None, writers=None, signatures=None, id=None, weight=None, label=None, cdate=None, ddate=None, nonreaders=None, tcdate=None, tmdate=None, tddate=None, tauthor=None)",
                    "docstring": "Initialize an Edge object"
                },
                {
                    "name": "to_json",
                    "signature": "to_json()",
                    "docstring": "Returns serialized json string for a given object"
                },
                {
                    "name": "from_json",
                    "signature": "from_json(e)",
                    "docstring": "Returns a deserialized object from a json string"
                }
            ]
        },
        {
            "name": "Tag",
            "docstring": """
    :param tag: Content of the tag
    :type tag: str
    :param invitation: Invitation id
    :type invitation: str
    :param readers: List of readers in the Invitation, each reader is a Group id
    :type readers: list[str]
    :param signature: Signature in the Invitation, signature is a Group id
    :type signature: str
    :param id: Tag id
    :type id: str, optional
    :param cdate: Creation date
    :type cdate: int, optional
    :param tcdate: True creation date
    :type tcdate: int, optional
    :param ddate: Deletion date
    :type ddate: int, optional
    :param forum: Forum id
    :type forum: str, optional
    :param nonreaders: List of nonreaders in the Invitation, each nonreader is a Group id
    :type nonreaders: list[str], optional""",
            "module": "openreview.api",
            "methods": [
                {
                    "name": "__init__",
                    "signature": "__init__(invitation, signature=None, tag=None, readers=None, writers=None, id=None, parent_invitations=None, cdate=None, tcdate=None, tmdate=None, ddate=None, forum=None, nonreaders=None, profile=None, weight=None, label=None, note=None)",
                    "docstring": "Initialize a Tag object"
                },
                {
                    "name": "to_json",
                    "signature": "to_json()",
                    "docstring": "Converts Tag instance to a dictionary. The instance variable names are the keys and their values the values of the dictinary."
                },
                {
                    "name": "from_json",
                    "signature": "from_json(t)",
                    "docstring": "Creates a Tag object from a dictionary that contains keys values equivalent to the name of the instance variables of the Tag class"
                }
            ]
        },
        {
            "name": "Edit",
            "docstring": """
    :param id: Edit id
    :type id: str
    :param readers: List of readers in the Edit, each reader is a Group id
    :type readers: list[str], optional
    :param writers: List of writers in the Edit, each writer is a Group id
    :type writers: list[str], optional
    :param signatures: List of signatures in the Edit, each signature is a Group id
    :type signatures: list[str], optional
    :param note: Template of the Note that will be created
    :type note: dict, optional
    :param invitation: Template of the Invitation that will be created
    :type invitation: dict, optional
    :param nonreaders: List of nonreaders in the Edit, each nonreader is a Group id
    :type nonreaders: list[str], optional
    :param cdate: Creation date
    :type cdate: int, optional
    :param ddate: Deletion date
    :type ddate: int, optional
    :param tcdate: True creation date
    :type tcdate: int, optional
    :param tmdate: Modification date
    :type tmdate: int, optional""",
            "module": "openreview.api",
            "methods": [
                {
                    "name": "__init__",
                    "signature": "__init__(id=None, domain=None, invitations=None, readers=None, writers=None, signatures=None, content=None, note=None, group=None, invitation=None, nonreaders=None, cdate=None, tcdate=None, tmdate=None, ddate=None, tauthor=None)",
                    "docstring": "Initialize an Edit object"
                },
                {
                    "name": "to_json",
                    "signature": "to_json()",
                    "docstring": "Converts Edit instance to a dictionary. The instance variable names are the keys and their values the values of the dictinary."
                },
                {
                    "name": "from_json",
                    "signature": "from_json(e)",
                    "docstring": "Creates an Edit object from a dictionary that contains keys values equivalent to the name of the instance variables of the Edit class"
                }
            ]
        },
        {
            "name": "LogRetry",
            "docstring": "Custom retry class for logging retry attempts",
            "module": "openreview.api",
            "methods": [
                {
                    "name": "__init__",
                    "signature": "__init__(*args, **kwargs)",
                    "docstring": "Initialize LogRetry"
                },
                {
                    "name": "increment",
                    "signature": "increment(method=None, url=None, response=None, error=None, _pool=None, _stacktrace=None)",
                    "docstring": "Log retry information before calling the parent class method"
                }
            ]
        }
    ]
    
    return classes


def search_openreview_functions(query: str) -> List[Dict[str, Any]]:
    """
    Search for functions by name or keyword in their docstrings.
    
    Args:
        query: Search term to match against function names and docstrings
        
    Returns:
        List of matching function dictionaries
        
    TODO: Implement advanced search:
    1. Fuzzy string matching
    2. Search in parameter names and types
    3. Search in return type information
    4. Rank results by relevance
    5. Support regex patterns
    """
    functions = get_openreview_functions()
    query_lower = query.lower()
    
    # Simple string matching implementation
    matching_functions = []
    for func in functions:
        if (query_lower in func["name"].lower() or 
            query_lower in func.get("docstring", "").lower()):
            matching_functions.append(func)
    
    return matching_functions


def get_library_overview() -> Dict[str, Any]:
    """
    Get a comprehensive overview of the openreview-py library.

    Returns a dictionary with:
    - functions: All available functions
    - classes: All available classes
    - modules: Module structure
    - statistics: Counts and metadata
    - api_versions: Information about API 1 vs API 2

    TODO: Implement comprehensive analysis:
    1. Module dependency mapping
    2. API endpoint coverage
    3. Version information extraction
    4. Examples and usage patterns
    5. Recent changes and deprecations
    """
    functions = get_openreview_functions()
    classes = get_openreview_classes()

    return {
        "functions": functions,
        "classes": classes,
        "modules": [
            "openreview",
            "openreview.api",
            "openreview.tools",
            "openreview.venue"
        ],
        "statistics": {
            "total_functions": len(functions),
            "total_classes": len(classes),
            "total_modules": 4
        },
        "api_versions": {
            "api_1": {
                "client_class": "openreview.Client",
                "baseurl": "https://api.openreview.net",
                "description": "Legacy API for older venues"
            },
            "api_2": {
                "client_class": "openreview.api.OpenReviewClient",
                "baseurl": "https://api2.openreview.net",
                "description": "Current API (preferred) - documented in this overview"
            },
            "important_note": "Use get_api_version_guide tool for detailed guidance on which API to use"
        },
        "version": "unknown",  # TODO: Extract from package
        "last_updated": "2024-01-01"  # TODO: Get real timestamp
    }
