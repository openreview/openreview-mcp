"""Synthetic conference tests for the test-suite index."""


class TestConferenceDecisions:
    def test_post_decisions(self, client, helpers, openreview_client):
        pc_client = client
        pc_client.post_note_edit(
            invitation='Conf25.cc/2025/Conference/Submission1/-/Decision',
            signatures=['Conf25.cc/2025/Conference/Program_Chairs'],
            note={'decision': {'value': 'Accept (Oral)'}},
            await_process=True,
        )
        helpers.await_queue_edit(
            openreview_client,
            invitation='Conf25.cc/2025/Conference/-/Decision',
        )

    def test_post_meta_review(self, client, helpers):
        client.post_note_edit(
            invitation='Conf25.cc/2025/Conference/Submission1/-/Meta_Review',
            signatures=['Conf25.cc/2025/Conference/Submission1/Area_Chair_x'],
            note={'recommendation': {'value': 'Accept'}},
        )


def test_post_submission(openreview_client, helpers):
    """Submit a paper via post_note_edit."""
    openreview_client.post_note_edit(
        invitation='Conf25.cc/2025/Conference/-/Submission',
        signatures=['~Author_Name1'],
        note={
            'title': {'value': 'Paper'},
            'abstract': {'value': 'Abstract here.'},
        },
    )
    helpers.await_queue_edit(openreview_client)
