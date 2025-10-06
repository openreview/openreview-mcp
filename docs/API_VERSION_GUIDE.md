# OpenReview API Version Guide

This document explains how the MCP server helps users and LLMs understand when to use API 1 vs API 2.

## Overview

OpenReview has two API versions that are often confused by users and LLMs. The MCP server now includes comprehensive guidance to prevent these mistakes.

## New Tool: `get_api_version_guide`

This tool provides complete information about:

### 1. API Version Differences

- **API 1**: Legacy API
  - Client: `openreview.Client`
  - Base URL: `https://api.openreview.net`
  - Used for older venues

- **API 2**: Current API (preferred)
  - Client: `openreview.api.OpenReviewClient`
  - Base URL: `https://api2.openreview.net`
  - Used for new venues and most operations

### 2. Decision Logic

The tool provides clear decision logic for:

#### Venue Request Forms (Exception)
- **Identifier**: Invitation starts with `OpenReview.net/Support/-/`
- **API**: ALWAYS API 1
- **Important**: This is true regardless of the venue's API version

#### Determining Venue API Version
1. Use API 2 client to retrieve venue root group
2. Check if group has `domain` property
3. If `domain` exists → API 2 venue
4. If `domain` doesn't exist → API 1 venue

#### Profiles
- **Default**: Always use API 2
- **Note**: Accessible from both APIs, but API 2 is preferred

### 3. Common Mistakes

The tool documents 4 common mistakes:
1. Using wrong API client for venue operations
2. Assuming all venues are in API 2
3. Using API 1 client for venue request forms
4. Using API 1 client for profiles unnecessarily

### 4. Best Practices

Six best practices are provided:
1. Default to API 2 for all new code
2. Always check domain group for venue operations
3. Remember venue request forms are always API 2
4. Use API 2 when in doubt (it can access both APIs)
5. Document API version in code
6. Test with both versions for legacy venue support

### 5. Quick Reference

**Use API 2 for:**
- New venues
- Venue request forms
- User profiles
- General searches
- Venues with `domain` property

**Use API 1 for:**
- Legacy venues (no `domain` property)
- Specific API 1 operations when required

## Integration Points

### 1. Dedicated Tool
The `get_api_version_guide` tool is the primary source of API version information.

**Usage by LLM:**
```
When user asks about OpenReview API or venue operations:
1. Call get_api_version_guide to understand which API to use
2. Check decision_logic section for specific scenarios
3. Follow best_practices for implementation
```

### 2. Library Overview
The `get_openreview_overview` tool now includes:
- Reference to both API versions
- Pointer to `get_api_version_guide` for detailed guidance

### 3. Server Capabilities
The tool is prominently listed in server startup output as "(IMPORTANT!)"

## Example Usage Scenarios

### Scenario 1: Venue Request Form
```python
# User wants to work with venue request form
invitation = "OpenReview.net/Support/-/Venue_Request"

# MCP server guides: ALWAYS use API 1
client = openreview.Client(baseurl='https://api.openreview.net')
notes = client.get_notes(invitation=invitation)
```

### Scenario 2: Unknown Venue
```python
# User wants to work with a venue but doesn't know API version
venue_id = "ICLR.cc/2023/Conference"

# MCP server guides: Check domain property
api2_client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')
group = api2_client.get_group(venue_id)

if hasattr(group, 'domain') and group.domain:
    # API 2 venue
    client = api2_client
else:
    # API 1 venue
    client = openreview.Client(baseurl='https://api.openreview.net')

# Now use correct client
submissions = client.get_notes(invitation=f'{venue_id}/-/Submission')
```

### Scenario 3: Profiles
```python
# User wants to retrieve profiles
# MCP server guides: ALWAYS prefer API 2

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')
profile = client.get_profile('~User_Name1')
```

## Benefits

### For Users
- Clear guidance prevents API version confusion
- Reduces trial-and-error debugging
- Comprehensive examples for each scenario

### For LLMs
- Structured decision logic for systematic approach
- Common mistakes section prevents errors
- Quick reference for fast decision-making

### For Developers
- Centralized API version knowledge
- Easy to update as APIs evolve
- Consistent guidance across all MCP interactions

## Testing

The tool has been tested and verified:
- ✅ Tool successfully registered (7 tools total)
- ✅ Comprehensive guidance structure
- ✅ All decision scenarios covered
- ✅ Examples and best practices included

## Future Enhancements

Potential improvements:
1. Add real-time API version detection for specific venues
2. Include schema difference examples
3. Add migration guide from API 1 to API 2
4. Integrate with actual OpenReview API to validate venue API versions
5. Add caching for venue API version lookups

## Maintenance

When updating this guide:
1. Update `get_api_version_guide` tool in `src/server.py`
2. Test with real scenarios
3. Update this documentation
4. Consider adding to `get_openreview_overview` if major changes

## Related Files

- `src/server.py` - Contains `get_api_version_guide` tool implementation
- `src/introspect.py` - Contains `get_library_overview` with API version references
- `DEPLOYMENT.md` - Production deployment guide (updated ports to 3000)
