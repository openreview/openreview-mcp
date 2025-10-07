"""FastMCP server for exposing openreview-py library structure."""

import logging
import os
import datetime
from typing import Any, Dict
from logging.handlers import RotatingFileHandler

from fastmcp import FastMCP, Context
from fastmcp.utilities.logging import get_logger
from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware, RetryMiddleware

from src.introspect import (
    get_openreview_classes,
    get_openreview_functions,
    search_openreview_functions,
    get_openreview_tools,
    get_library_overview
)

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Generate timestamp for log file
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f"logs/openreview_mcp_{timestamp}.log"

# Setup logging with rotation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(process)d - %(thread)d - %(message)s',
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        ),
        logging.FileHandler("openreview_mcp.log")  # Keep a current log file too
    ]
)

# Get FastMCP logger for server-side logging
logger = get_logger("openreview_mcp")

# Initialize FastMCP server
mcp = FastMCP(
    name="OpenReview Python Library Expert",
    instructions="""Expert assistant for the openreview-py Python library. Use this server when users need help with:
- Writing Python code to interact with OpenReview's academic peer review platform
- Understanding OpenReview API methods, classes, and data structures
- Finding the right functions for tasks like retrieving submissions, reviews, profiles, venues
- Learning about API 1 vs API 2 differences (CRITICAL: always check API version guide first!)
- Searching for specific OpenReview operations by keyword or task
- Getting complete documentation for OpenReview Python client methods

IMPORTANT: If the user mentions venues, conferences, submissions, or API versions, ALWAYS use get_api_version_guide first to understand which client to use.""",
    version="0.1.0"
)


@mcp.tool()
async def get_server_capabilities(ctx: Context) -> Dict[str, Any]:
    """
    Discover all available OpenReview library exploration tools and their purposes.

    USE THIS WHEN: User asks "what can you help me with" or "what tools are available" regarding OpenReview.

    This tool provides a complete catalog of available exploration capabilities including:
    - Tools for searching OpenReview functions by keyword
    - Tools for browsing classes and methods
    - Tools for understanding API versions (API 1 vs API 2)
    - Tools for getting detailed function documentation

    Returns:
        Dictionary containing server metadata, tool list, and usage guidance
    """
    # Server-side logging
    logger.info("Retrieving server capabilities information")

    # Client-side logging
    await ctx.info("Requesting server capabilities")

    try:
        # Collect all tools metadata (get_tools returns list of tool names)
        tool_names = await mcp.get_tools()

        # Build capabilities response
        capabilities = {
            "server_info": {
                "name": mcp.name,
                "instructions": mcp.instructions,
                "version": mcp.version,
            },
            "tools": tool_names,
            "tool_count": len(tool_names),
            "timestamp": datetime.datetime.now().isoformat()
        }

        logger.info(f"Returning capabilities with {len(tool_names)} available tools")

        await ctx.info("Server capabilities retrieved successfully",
                     extra={"tool_count": len(tool_names)})

        return capabilities
    except Exception as e:
        logger.error(f"Error retrieving server capabilities: {str(e)}", exc_info=True)
        await ctx.error(f"Failed to retrieve server capabilities: {str(e)}")
        raise


@mcp.tool()
async def list_openreview_functions(ctx: Context, filter_by_module: str = None) -> Dict[str, Any]:
    """
    Browse ALL available methods from the OpenReview Python client for interacting with the OpenReview platform.

    USE THIS WHEN:
    - User wants to see what operations are available in OpenReview
    - User asks "what can I do with OpenReview" or "show me all functions"
    - You need to browse available methods before choosing the right one
    - User wants to explore the full API surface area

    This returns methods from OpenReviewClient including:
    - Note/submission operations (get_notes, post_note_edit, search_notes)
    - Group/venue operations (get_group, get_groups, post_group_edit)
    - Profile operations (get_profile, search_profiles, post_profile)
    - Invitation operations (get_invitation, get_invitations)
    - Edge/relationship operations (get_edges, post_edge)
    - Tag operations (get_tags, post_tag)
    - Authentication (login_user, impersonate)
    - File operations (get_pdf, get_attachment)
    - Messaging (post_message, get_messages)
    - Expertise/matching (request_expertise, get_expertise_results)

    WORKFLOW: After using this, use get_function_details() with a specific function name to see detailed documentation.

    Args:
        filter_by_module: Optional - filter by 'openreview.api' for API 2 methods or 'openreview' for API 1 methods

    Returns:
        JSON object with 'functions' array containing: name, signature, docstring, module, function_type
    """
    # Server-side logging
    logger.info(f"Listing OpenReview functions with filter: {filter_by_module}")

    # Client-side logging
    await ctx.info(f"Retrieving OpenReview functions",
                  extra={"filter_module": filter_by_module})

    try:
        functions = get_openreview_functions()

        # TODO: Implement more sophisticated filtering
        # - Filter by function type (constructor, method, function)
        # - Filter by parameter count or complexity
        # - Sort by relevance or alphabetical order
        if filter_by_module:
            functions = [f for f in functions if f.get("module") == filter_by_module]

        # Log the results
        logger.info(f"Found {len(functions)} functions matching criteria")

        await ctx.info(f"Found {len(functions)} functions",
                      extra={"count": len(functions)})

        # Standardize the response format
        return {
            "status": "success",
            "count": len(functions),
            "functions": functions,
            "metadata": {
                "timestamp": datetime.datetime.now().isoformat(),
                "filter": filter_by_module
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving functions: {str(e)}", exc_info=True)
        await ctx.error(f"Failed to retrieve functions: {str(e)}")
        raise


@mcp.tool()
async def list_openreview_classes(ctx: Context, include_methods: bool = True) -> Dict[str, Any]:
    """
    Explore all OpenReview data model classes and client classes for understanding the object structure.

    USE THIS WHEN:
    - User asks about OpenReview data structures, objects, or models
    - User needs to understand what fields/properties a Note, Group, Profile, or Edge has
    - User wants to know the difference between Client and OpenReviewClient classes
    - User asks "how do I create a Note/Group/Edge object"
    - You need to understand constructor parameters or class initialization

    This returns comprehensive information about core OpenReview classes:
    - Client: Legacy API 1 client (for older venues and venue request forms)
    - OpenReviewClient: Modern API 2 client (preferred for most operations)
    - Note: Represents submissions, reviews, comments (contains content, signatures, readers)
    - Group: Represents venues, committees, user groups (contains members, readers, domain)
    - Profile: User profiles with emails, publications, history, expertise
    - Invitation: Defines what types of content can be created (Note/Edge/Tag templates)
    - Edge: Represents relationships (assignments, conflicts, recommendations)
    - Tag: Metadata annotations (decisions, ratings, labels)
    - Edit: Represents changes to Notes/Groups/Invitations

    WORKFLOW: After identifying the class, use list_openreview_functions() or search_openreview_api() to find methods that work with these objects.

    Args:
        include_methods: Set to True (default) to see all class methods, False for just class structure

    Returns:
        JSON object with 'classes' array containing: name, docstring, module, methods (if requested)
    """
    # Server-side logging
    logger.info(f"Listing OpenReview classes with include_methods={include_methods}")

    # Client-side logging
    await ctx.info("Retrieving OpenReview classes",
                  extra={"include_methods": include_methods})

    try:
        classes = get_openreview_classes()

        # TODO: Add more filtering options:
        # - Filter by inheritance hierarchy
        # - Filter by class type (abstract, concrete, mixin)
        # - Include/exclude private methods
        # - Add property information
        if not include_methods:
            for cls in classes:
                cls.pop("methods", None)

        # Log the results
        method_count = sum(len(cls.get("methods", [])) for cls in classes if include_methods)
        logger.info(f"Found {len(classes)} classes with {method_count} methods")

        await ctx.info(f"Found {len(classes)} classes",
                      extra={
                          "class_count": len(classes),
                          "method_count": method_count if include_methods else 0
                      })

        # Standardize the response format
        return {
            "status": "success",
            "count": len(classes),
            "classes": classes,
            "metadata": {
                "timestamp": datetime.datetime.now().isoformat(),
                "include_methods": include_methods,
                "method_count": method_count if include_methods else 0
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving classes: {str(e)}", exc_info=True)
        await ctx.error(f"Failed to retrieve classes: {str(e)}")
        raise


@mcp.tool()
async def search_openreview_api(query: str, ctx: Context) -> Dict[str, Any]:
    """
    Find the right OpenReview function by searching with keywords, task descriptions, or operation names.

    USE THIS WHEN:
    - User describes what they want to do (e.g., "get submissions", "find reviewers", "send email")
    - User mentions a specific operation or task without knowing the exact function name
    - You need to find functions related to a concept (e.g., "profile", "venue", "paper", "review")
    - User asks "how do I..." followed by an action
    - User asks about proof of service, reviewer history, or CV documentation

    SEARCHES ACROSS:
    - All OpenReviewClient methods (get_notes, post_message, etc.)
    - All utility tools from openreview.tools (get_profiles, get_own_reviews)

    SEARCH EXAMPLES:
    - "note" → finds get_note, get_notes, post_note_edit, search_notes, delete_note
    - "profile" → finds get_profile, get_profiles, search_profiles, post_profile, tools.get_profiles
    - "group" → finds get_group, get_groups, post_group_edit, add_members_to_group
    - "submission" → finds functions related to paper submissions
    - "email" or "message" → finds post_message, get_messages
    - "pdf" → finds get_pdf, put_attachment
    - "invitation" → finds get_invitation, get_invitations, post_invitation_edit
    - "review" or "reviewer service" → finds get_own_reviews (utility tool)
    - "batch" or "bulk" → finds tools.get_profiles for batch operations
    - "proof" or "letter" or "CV" → finds get_own_reviews

    The search looks through function names AND documentation, so you can search by:
    - Function names (partial matches work)
    - Keywords in descriptions
    - Operation types (get, post, delete, search)
    - Object types (note, group, edge, profile, tag, review)
    - Use cases (proof of service, batch operations, CV building)

    WORKFLOW: After finding relevant functions, use get_function_details() or get_utility_tools() to see complete documentation and parameters.

    Args:
        query: Search keyword or phrase (e.g., "get submissions", "profile", "reviewer service", "batch fetch", "pdf")

    Returns:
        JSON object with 'results' array of matching functions including: name, signature, docstring, module
    """
    # Server-side logging
    logger.info(f"Searching OpenReview API with query: '{query}'")

    # Client-side logging
    await ctx.info(f"Searching for '{query}'")

    try:
        # Parameter validation
        if not isinstance(query, str):
            error_msg = f"Expected query to be a string, got {type(query).__name__}"
            logger.error(error_msg)
            await ctx.error(error_msg)
            raise TypeError(error_msg)

        if not query or not query.strip():
            logger.warning("Empty search query received")
            await ctx.warning("Empty search query provided, returning empty results")
            return {"status": "success", "count": 0, "results": [], "metadata": {"timestamp": datetime.datetime.now().isoformat(), "query": query}}
        
        # TODO: Enhance search capabilities:
        # - Search across both functions and classes
        # - Implement fuzzy matching
        # - Add search result ranking
        # - Support advanced query syntax (AND, OR, NOT)
        # - Search in parameter names and types
        matching_functions = search_openreview_functions(query.strip())
        
        # TODO: Also search classes and their methods
        # matching_classes = search_openreview_classes(query.strip())
        # return matching_functions + matching_classes
        
        # Log the results
        logger.info(f"Found {len(matching_functions)} functions matching query '{query}'")

        await ctx.info(f"Found {len(matching_functions)} matching functions",
                      extra={
                          "query": query,
                          "match_count": len(matching_functions)
                      })

        # Standardize the response format
        return {
            "status": "success",
            "count": len(matching_functions),
            "results": matching_functions,
            "metadata": {
                "timestamp": datetime.datetime.now().isoformat(),
                "query": query
            }
        }
    except Exception as e:
        logger.error(f"Error searching API with query '{query}': {str(e)}", exc_info=True)
        await ctx.error(f"Search failed: {str(e)}")
        raise


@mcp.tool()
async def get_openreview_overview(ctx: Context) -> Dict[str, Any]:
    """
    Get a high-level summary of the entire OpenReview Python library including statistics and organization.

    USE THIS WHEN:
    - User asks for a "summary" or "overview" of the OpenReview library
    - User wants to understand the library structure before diving into specifics
    - You need to see the big picture of available modules, class counts, and function counts
    - User is new to OpenReview and wants to know what's available

    This provides:
    - Total counts of functions, classes, and tools available
    - List of all modules (openreview, openreview.api, openreview.tools, openreview.venue)
    - Brief descriptions of API 1 vs API 2
    - High-level library organization and structure

    INCLUDES:
    - All available functions (extracted from OpenReviewClient methods)
    - All available classes (Client, OpenReviewClient, Note, Group, Profile, Edge, Tag, etc.)
    - Utility tools from openreview.tools module (like get_profiles helper)
    - Module structure and statistics
    - API version information

    WORKFLOW: Use this first for orientation, then use more specific tools like search_openreview_api() or list_openreview_functions() to explore details.

    Returns:
        Comprehensive dictionary with: functions, classes, tools, modules, statistics, and API version info
    """
    # Server-side logging
    logger.info("Retrieving OpenReview library overview")

    # Client-side logging
    await ctx.info("Generating OpenReview library overview")
    await ctx.debug("This may take a moment as we collect comprehensive information about the library")

    try:
        overview = get_library_overview()

        # TODO: Add more comprehensive information:
        # - Recent changes and version history
        # - Usage examples for common patterns
        # - API endpoint mappings
        # - Error handling patterns
        # - Configuration options

        # Extract key statistics for logging
        func_count = len(overview.get("functions", []))
        class_count = len(overview.get("classes", []))
        module_count = len(overview.get("modules", []))

        # Server-side logging
        logger.info(f"Overview generated: {func_count} functions, {class_count} classes, {module_count} modules")

        # Client-side logging
        await ctx.info("Overview generation complete",
                      extra={
                          "function_count": func_count,
                          "class_count": class_count,
                          "module_count": module_count
                      })

        return overview
    except Exception as e:
        logger.error(f"Error generating library overview: {str(e)}", exc_info=True)
        await ctx.error(f"Failed to generate library overview: {str(e)}")
        raise


@mcp.tool()
async def get_function_details(function_name: str, ctx: Context) -> Dict[str, Any]:
    """
    Get complete documentation for a specific OpenReview function including signature, parameters, and usage info.

    USE THIS WHEN:
    - User asks for details about a specific function by name
    - You found a function via search and need its full documentation
    - User wants to know the exact parameters and what they mean
    - You need to understand how to call a specific method

    COMMON FUNCTION NAMES TO LOOK UP:
    - get_notes, get_note, post_note_edit (for submissions, reviews, comments)
    - get_group, get_groups, post_group_edit (for venues, committees, groups)
    - get_profile, get_profiles, search_profiles (for user profiles)
    - get_invitation, get_invitations (for invitation templates)
    - get_edges, post_edge (for assignments, conflicts, relationships)
    - get_tags, post_tag (for decisions, ratings, metadata)
    - post_message, get_messages (for email notifications)
    - get_pdf, get_attachment, put_attachment (for file operations)
    - login_user, impersonate (for authentication)
    - search_notes (for full-text search)
    - request_expertise, get_expertise_results (for reviewer matching)

    Provides:
    - Full function signature with parameter names and defaults
    - Complete docstring with parameter descriptions
    - Module location (openreview.api.OpenReviewClient or openreview.Client)
    - Function type (method, constructor, etc.)

    WORKFLOW: Use search_openreview_api() first to find candidates, then use this to get complete details.

    Args:
        function_name: Exact function name (e.g., "get_notes", "post_message", "search_profiles")

    Returns:
        Dictionary with: name, signature, docstring, module, parameters (if available), return_type
    """
    # Server-side logging
    logger.info(f"Retrieving details for function: '{function_name}'")

    # Client-side logging
    await ctx.info(f"Looking up details for function '{function_name}'")

    try:
        # Parameter validation
        if not isinstance(function_name, str):
            error_msg = f"Expected function_name to be a string, got {type(function_name).__name__}"
            logger.error(error_msg)
            await ctx.error(error_msg)
            raise TypeError(error_msg)

        if not function_name:
            error_msg = "Empty function name provided"
            logger.warning(error_msg)
            await ctx.warning(error_msg)
            return {"error": error_msg}

        functions = get_openreview_functions()

        # Find the function by name
        for func in functions:
            if func["name"] == function_name:
                # TODO: Add more detailed information:
                # - Parameter types and descriptions
                # - Return type information
                # - Usage examples
                # - Related functions
                # - Error conditions
                result = {
                    **func,
                    "parameters": [],  # TODO: Extract parameter info
                    "return_type": func.get("return_type", "unknown"),
                    "examples": [],  # TODO: Add usage examples
                    "related_functions": []  # TODO: Find related functions
                }

                # Log successful retrieval
                logger.info(f"Found function details for '{function_name}'")

                module = func.get("module", "unknown")
                signature = func.get("signature", "unknown")
                await ctx.info(f"Retrieved details for function '{function_name}'",
                              extra={
                                  "function_name": function_name,
                                  "module": module,
                                  "signature": signature
                              })

                return result

        # Function not found
        error_msg = f"Function '{function_name}' not found"
        logger.warning(error_msg)

        await ctx.warning(error_msg)

        return {"error": error_msg}
    except Exception as e:
        logger.error(f"Error retrieving function details: {str(e)}", exc_info=True)
        await ctx.error(f"Failed to retrieve function details: {str(e)}")
        raise


@mcp.tool()
async def get_utility_tools(ctx: Context) -> Dict[str, Any]:
    """
    Get powerful utility helper functions from openreview.tools module for advanced operations.

    USE THIS WHEN:
    - User needs to fetch many profiles at once (more than 1000)
    - User wants to get profiles with publications, relations, or preferred emails
    - User asks about "batch operations" or "bulk fetching"
    - User asks "How do I get proof of my reviewer service?" or "Can I see my reviews?"
    - User asks about reviewer letters, proof of service, or CV documentation
    - You need helper functions that wrap complex multi-step operations
    - User mentions limitations of the standard client methods

    UTILITY FUNCTIONS AVAILABLE:

    1. get_profiles(client, ids_or_emails, ...):
       - Fetch profiles in batches (handles >1000 profiles automatically)
       - Supports profile IDs (~Username1) and email addresses
       - Creates placeholder profiles for unconfirmed emails
       - Options to include publications from both API 1 and API 2
       - Options to recursively fetch related profiles
       - Options to get preferred email addresses
       - Can return as dict for easy lookup by id/email

       WHY USE THIS:
       - client.get_profiles() is limited to 1000 profiles
       - Handles pagination automatically
       - Enriches profiles with publications and relations
       - Handles mixed inputs (IDs and emails together)
       - More efficient for large-scale profile operations

    2. get_own_reviews(client):
       - Retrieve ALL public reviews written by the authenticated user
       - Works across both API 1 and API 2 venues automatically
       - Returns submission titles with direct links to submissions and reviews
       - Useful for documenting reviewer service, CV building, or proof of work

       WHY USE THIS:
       - Users often need to compile reviewing history for documentation
       - OpenReview doesn't auto-generate reviewer certificates (contact organizers)
       - Returns only public reviews (protects confidential ones)
       - Alternative to manually checking openreview.net/activity
       - Provides direct links for easy sharing/reference

    WORKFLOW: Use this when standard client methods (from list_openreview_functions) are not sufficient for complex or bulk operations.

    Returns:
        Array of utility tools with detailed parameters, defaults, usage examples, and documentation
    """
    logger.info("Retrieving utility tools information")
    await ctx.info("Providing openreview.tools utility functions documentation")

    try:
        tools = get_openreview_tools()

        logger.info(f"Found {len(tools)} utility tools")
        await ctx.info(f"Retrieved {len(tools)} utility tools",
                      extra={"tool_count": len(tools)})

        return {
            "status": "success",
            "count": len(tools),
            "tools": tools,
            "metadata": {
                "module": "openreview.tools",
                "description": "Advanced utility functions that wrap complex operations"
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving utility tools: {str(e)}", exc_info=True)
        await ctx.error(f"Failed to retrieve utility tools: {str(e)}")
        raise


@mcp.tool()
async def get_api_version_guide(ctx: Context) -> Dict[str, Any]:
    """
    CRITICAL: Understand the difference between OpenReview API 1 vs API 2 and which client to use.

    ⚠️ USE THIS FIRST WHEN:
    - User mentions a venue, conference, or workshop
    - User wants to retrieve submissions, reviews, or venue data
    - User asks about "Client" vs "OpenReviewClient"
    - Working with venue request forms
    - Code involves baseurl parameters
    - You're unsure which API version to use

    WHY THIS IS CRITICAL:
    OpenReview has TWO separate APIs with different clients, base URLs, and data schemas:
    - API 1 (openreview.Client) → https://api.openreview.net → Older venues + venue request forms
    - API 2 (openreview.api.OpenReviewClient) → https://api2.openreview.net → Modern venues (preferred)

    Using the WRONG API means:
    ❌ Data won't be found
    ❌ Schema mismatches cause errors
    ❌ Operations fail silently

    THIS GUIDE PROVIDES:
    - How to determine if a venue uses API 1 or API 2 (check for 'domain' property)
    - When to use openreview.Client vs openreview.api.OpenReviewClient
    - Special case: Venue request forms are ALWAYS API 1
    - Special case: User profiles should use API 2
    - Client instantiation examples for both APIs
    - Decision tree and workflow for choosing the right API
    - Common mistakes and how to avoid them

    DECISION LOGIC:
    1. Venue request forms (invitation starts with "OpenReview.net/Support/-/") → ALWAYS API 1
    2. For other venues: Check domain property on venue group:
       - Has 'domain' property → API 2
       - No 'domain' property → API 1
    3. User profiles → Always prefer API 2
    4. New code → Default to API 2 unless working with legacy venues

    Returns:
        Comprehensive guide with API differences, decision logic, examples, and best practices
    """
    logger.info("Retrieving API version guidance")
    await ctx.info("Providing OpenReview API version guidance")

    guide = {
        "summary": "OpenReview has two API versions with different clients, base URLs, and data schemas",

        "api_versions": {
            "api_1": {
                "client_class": "openreview.Client",
                "baseurl": "https://api.openreview.net",
                "description": "Legacy API, used for older venues and some current operations",
                "instantiation_example": "client = openreview.Client(baseurl='https://api.openreview.net', username='user', password='pass')"
            },
            "api_2": {
                "client_class": "openreview.api.OpenReviewClient",
                "baseurl": "https://api2.openreview.net",
                "description": "Current API, preferred for new venues and most operations",
                "instantiation_example": "client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net', username='user', password='pass')"
            }
        },

        "key_differences": {
            "data_storage": "New data is usually stored in API 2",
            "schemas": "Notes, invitations, groups, edges, and tags have slightly different schemas between versions",
            "compatibility": "API 2 client can retrieve groups from both APIs, but API 1 client is limited to API 1"
        },

        "decision_logic": {
            "venue_request_forms": {
                "description": "Special documents related to venue setup and configuration",
                "identifier": "Check if invitation field starts with 'OpenReview.net/Support/-/'",
                "api_to_use": "These are ALWAYS in API 1",
                "client": "openreview.Client",
                "note": "This is the ONLY exception - venue request forms are always API 1 regardless of venue API version"
            },

            "determining_venue_api": {
                "description": "How to determine if a venue uses API 1 or API 2",
                "method": "Retrieve the venue root group (domain group) using API 2 client",
                "steps": [
                    "1. Instantiate an openreview.api.OpenReviewClient with baseurl='https://api2.openreview.net'",
                    "2. Use client.get_group(venue_id) to retrieve the venue root group",
                    "3. Check if the returned group has a 'domain' property",
                    "4. If 'domain' property exists: venue is API 2 - use openreview.api.OpenReviewClient for ALL venue data",
                    "5. If 'domain' property does NOT exist: venue is API 1 - use openreview.Client for ALL venue data"
                ],
                "example": """
import openreview

# Always start with API 2 client to check
api2_client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')
group = api2_client.get_group('Conference.com/2024')

if hasattr(group, 'domain') and group.domain:
    # API 2 venue - continue using api2_client
    notes = api2_client.get_notes(invitation='Conference.com/2024/-/Submission')
else:
    # API 1 venue - switch to API 1 client
    api1_client = openreview.Client(baseurl='https://api.openreview.net')
    notes = api1_client.get_notes(invitation='Conference.com/2024/-/Submission')
"""
            },

            "profiles": {
                "description": "User profiles can be accessed from either API",
                "recommendation": "ALWAYS prefer API 2 (openreview.api.OpenReviewClient) unless there's a specific reason to use API 1",
                "api_to_use": "API 2",
                "client": "openreview.api.OpenReviewClient",
                "baseurl": "https://api2.openreview.net",
                "note": "Profiles are accessible from both APIs but API 2 is the standard"
            },

            "general_operations": {
                "search": "Use API 2 by default",
                "new_venues": "Always API 2",
                "legacy_venues": "Determine using domain group check method above",
                "cross_api_queries": "API 2 client can retrieve groups from both APIs"
            }
        },

        "common_mistakes": {
            "mistake_1": {
                "error": "Using wrong API client for venue operations",
                "consequence": "Data not found or incorrect schema errors",
                "solution": "Always check venue's domain group first to determine correct API"
            },
            "mistake_2": {
                "error": "Assuming all venues are in API 2",
                "consequence": "Missing data from API 1 venues",
                "solution": "Use the domain property check method"
            },
            "mistake_3": {
                "error": "Using API 2 client for venue request forms",
                "consequence": "Cannot access venue request form data",
                "solution": "Venue request forms (invitation starts with 'OpenReview.net/Support/-/') are ALWAYS API 1"
            },
            "mistake_4": {
                "error": "Using API 1 client for profiles",
                "consequence": "Unnecessary complexity",
                "solution": "Always use API 2 for profiles unless specifically required otherwise"
            }
        },

        "best_practices": [
            "1. Default to API 2 (openreview.api.OpenReviewClient) for all new code",
            "2. For venue operations: Always check domain group first to determine API version",
            "3. Remember: Venue request forms are ALWAYS API 1, regardless of venue API",
            "4. When in doubt, use API 2 - it can access data from both APIs",
            "5. Document which API version you're using in your code comments",
            "6. Test with both API versions if supporting legacy venues"
        ],

        "quick_reference": {
            "use_api_2_for": [
                "New venues",
                "User profiles (default)",
                "General searches",
                "When venue domain group has 'domain' property"
            ],
            "use_api_1_for": [
                "Legacy venues (domain group lacks 'domain' property)",
                "Venue request forms (invitation starts with 'OpenReview.net/Support/-/')",
                "Specific API 1 operations when explicitly required"
            ]
        }
    }

    logger.info("API version guidance provided")
    await ctx.info("API version guidance retrieved successfully")

    return guide


@mcp.custom_route("/health", methods=["GET"])
async def health_check():
    """Health check endpoint for monitoring server availability."""
    return {
        "status": "healthy",
        "service": "openreview-mcp-server",
        "version": "0.1.0"
    }


def main():
    """Run the FastMCP server."""
    # TODO: Add configuration options:
    # - Custom port configuration
    # - Logging level settings
    # - Cache configuration for introspection results
    # - Module inclusion/exclusion filters
    # - Performance monitoring
    
    # Add advanced error handling middleware
    mcp.add_middleware(ErrorHandlingMiddleware(
        include_traceback=True,
        transform_errors=True
    ))

    # Add retry middleware for transient errors
    mcp.add_middleware(RetryMiddleware(
        max_retries=3
    ))

    # Log server startup
    logger.info("Starting OpenReview Python Library MCP Server")
    
    # Also print to console for user-friendly output
    print("=" * 80)
    print("🚀 OpenReview Python Library Expert - MCP Server Starting")
    print("=" * 80)
    print("\n📚 Available Tools for LLMs:\n")
    print("🔍 SEARCH & DISCOVER:")
    print("  • search_openreview_api - Find functions by keyword or task description")
    print("  • list_openreview_functions - Browse all available client methods")
    print("  • list_openreview_classes - Explore data model classes (Note, Group, etc.)")
    print("  • get_openreview_overview - High-level library summary and statistics")
    print()
    print("📖 DETAILED DOCUMENTATION:")
    print("  • get_function_details - Complete docs for a specific function")
    print("  • get_utility_tools - Advanced helper functions (batch operations)")
    print()
    print("⚠️  CRITICAL REFERENCE:")
    print("  • get_api_version_guide - API 1 vs API 2 decision guide (USE THIS FIRST!)")
    print()
    print("🔧 ADMINISTRATION:")
    print("  • get_server_capabilities - List all available tools")
    print()
    print("=" * 80)
    print("💡 TIP: Use get_api_version_guide when working with venues/conferences!")
    print("=" * 80)
    print()
    
    # Start the FastMCP server with HTTP transport
    # You can configure host/port via environment variables or here
    import os
    host = os.environ.get("MCP_HOST", "localhost")
    port = int(os.environ.get("MCP_PORT", "4000"))
    
    logger.info(f"Server configured with host={host}, port={port}")

    try:
        logger.info(f"Starting HTTP server on {host}:{port}...")
        mcp.run(transport="http", host=host, port=port, path="/mcp")
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
        print("\nServer stopped gracefully.")
    except Exception as e:
        logger.critical(f"Failed to start server: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
