# openreview-py Code Examples

## Authentication

### Connect to production

```python
import openreview

client = openreview.api.OpenReviewClient(
    baseurl='https://api2.openreview.net',
    username='user@example.com',
    password='your_password'
)
```

### Token-based auth

```python
client = openreview.api.OpenReviewClient(
    baseurl='https://api2.openreview.net',
    token='your_bearer_token'
)
```

## Notes

### Submit a paper

```python
from openreview.api import Note

result = client.post_note_edit(
    invitation='VenueID/-/Submission',
    signatures=['~Author_Name1'],
    note=Note(
        content={
            'title': {'value': 'My Paper Title'},
            'abstract': {'value': 'This paper presents...'},
            'authors': {'value': ['Alice Smith']},
            'authorids': {'value': ['~Alice_Smith1']}
        }
    ),
    await_process=True
)
```

## Conference Workflow

### Create venue via request form

```python
request_form = client.post_note(openreview.Note(
    invitation='openreview.net/Support/-/Request_Form',
    signatures=['~PC_Name1'],
    readers=['openreview.net/Support', '~PC_Name1'],
    writers=[],
    content={
        'title': 'Conference 2025',
        'Official Venue Name': 'Conference 2025',
        'Abbreviated Venue Name': 'Conf25'
    }
))
```

### Post a review

```python
from openreview.api import Note

reviewer_client.post_note_edit(
    invitation='Conf25/Submission1/-/Official_Review',
    signatures=['Conf25/Submission1/Reviewer_abc123'],
    note=Note(
        content={
            'review': {'value': 'This paper presents a novel approach...'},
            'rating': {'value': 8},
            'confidence': {'value': 4}
        }
    ),
    await_process=True
)
```
