# coding=utf-8
# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

import pytest
import functools
from azure.core.exceptions import HttpResponseError, ServiceRequestError, ClientAuthenticationError
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer._generated.models import AnalyzeOperationResult
from azure.ai.formrecognizer._response_handlers import prepare_content_result
from azure.ai.formrecognizer import FormRecognizerClient, FormRecognizerApiVersion
from testcase import FormRecognizerTest
from preparers import GlobalClientPreparer as _GlobalClientPreparer
from preparers import FormRecognizerPreparer


FormRecognizerClientPreparer = functools.partial(_GlobalClientPreparer, FormRecognizerClient)


class TestContentFromUrl(FormRecognizerTest):

    @FormRecognizerPreparer()
    def test_content_url_auth_bad_key(self, formrecognizer_test_endpoint, formrecognizer_test_api_key):
        client = FormRecognizerClient(formrecognizer_test_endpoint, AzureKeyCredential("xxxx"))
        with self.assertRaises(ClientAuthenticationError):
            poller = client.begin_recognize_content_from_url(self.invoice_url_pdf)

    @FormRecognizerPreparer()
    @FormRecognizerClientPreparer()
    def test_content_url_pass_stream(self, client):
        with open(self.receipt_jpg, "rb") as receipt:
            with self.assertRaises(HttpResponseError):
                poller = client.begin_recognize_content_from_url(receipt)

    @FormRecognizerPreparer()
    @FormRecognizerClientPreparer()
    def test_content_url_transform_pdf(self, client):
        responses = []

        def callback(raw_response, _, headers):
            analyze_result = client._deserialize(AnalyzeOperationResult, raw_response)
            extracted_layout = prepare_content_result(analyze_result)
            responses.append(analyze_result)
            responses.append(extracted_layout)

        poller = client.begin_recognize_content_from_url(self.invoice_url_pdf, cls=callback)
        result = poller.result()
        raw_response = responses[0]
        layout = responses[1]
        page_results = raw_response.analyze_result.page_results
        read_results = raw_response.analyze_result.read_results

        # Check form pages
        self.assertFormPagesTransformCorrect(layout, read_results, page_results)

    @FormRecognizerPreparer()
    @FormRecognizerClientPreparer()
    def test_content_url_pdf(self, client):
        poller = client.begin_recognize_content_from_url(self.invoice_url_pdf)
        result = poller.result()
        self.assertEqual(len(result), 1)
        layout = result[0]
        self.assertEqual(layout.page_number, 1)
        self.assertFormPagesHasValues(result)
        self.assertEqual(layout.tables[0].row_count, 3)
        self.assertEqual(layout.tables[0].column_count, 5)
        self.assertEqual(layout.tables[0].page_number, 1)

    @FormRecognizerPreparer()
    @FormRecognizerClientPreparer()
    def test_content_url_transform_jpg(self, client):
        responses = []

        def callback(raw_response, _, headers):
            analyze_result = client._deserialize(AnalyzeOperationResult, raw_response)
            extracted_layout = prepare_content_result(analyze_result)
            responses.append(analyze_result)
            responses.append(extracted_layout)

        poller = client.begin_recognize_content_from_url(self.form_url_jpg, cls=callback)
        result = poller.result()
        raw_response = responses[0]
        layout = responses[1]
        page_results = raw_response.analyze_result.page_results
        read_results = raw_response.analyze_result.read_results

        # Check form pages
        self.assertFormPagesTransformCorrect(layout, read_results, page_results)

    @FormRecognizerPreparer()
    @FormRecognizerClientPreparer()
    def test_content_url_jpg(self, client):
        poller = client.begin_recognize_content_from_url(self.form_url_jpg)
        result = poller.result()
        self.assertEqual(len(result), 1)
        layout = result[0]
        self.assertEqual(layout.page_number, 1)
        self.assertFormPagesHasValues(result)
        self.assertEqual(layout.tables[0].row_count, 5)
        self.assertEqual(layout.tables[0].column_count, 4)
        self.assertEqual(layout.tables[1].row_count, 4)
        self.assertEqual(layout.tables[1].column_count, 2)
        self.assertEqual(layout.tables[0].page_number, 1)
        self.assertEqual(layout.tables[1].page_number, 1)

    @FormRecognizerPreparer()
    @FormRecognizerClientPreparer()
    def test_content_multipage_url(self, client):
        poller = client.begin_recognize_content_from_url(self.multipage_url_pdf)
        result = poller.result()

        self.assertEqual(len(result), 3)
        self.assertFormPagesHasValues(result)

    @FormRecognizerPreparer()
    @FormRecognizerClientPreparer()
    def test_content_multipage_transform_url(self, client):
        responses = []

        def callback(raw_response, _, headers):
            analyze_result = client._deserialize(AnalyzeOperationResult, raw_response)
            extracted_layout = prepare_content_result(analyze_result)
            responses.append(analyze_result)
            responses.append(extracted_layout)

        poller = client.begin_recognize_content_from_url(self.multipage_url_pdf, cls=callback)
        result = poller.result()
        raw_response = responses[0]
        layout = responses[1]
        page_results = raw_response.analyze_result.page_results
        read_results = raw_response.analyze_result.read_results

        # Check form pages
        self.assertFormPagesTransformCorrect(layout, read_results, page_results)

    @FormRecognizerPreparer()
    @FormRecognizerClientPreparer()
    @pytest.mark.live_test_only
    def test_content_continuation_token(self, client):
        initial_poller = client.begin_recognize_content_from_url(self.form_url_jpg)
        cont_token = initial_poller.continuation_token()

        poller = client.begin_recognize_content_from_url(None, continuation_token=cont_token)
        result = poller.result()
        self.assertIsNotNone(result)
        initial_poller.wait()  # necessary so azure-devtools doesn't throw assertion error

    @FormRecognizerPreparer()
    @FormRecognizerClientPreparer()
    def test_content_multipage_table_span_pdf(self, client):
        poller = client.begin_recognize_content_from_url(self.multipage_table_url_pdf)
        result = poller.result()
        self.assertEqual(len(result), 2)
        layout = result[0]
        self.assertEqual(layout.page_number, 1)
        self.assertEqual(len(layout.tables), 2)
        self.assertEqual(layout.tables[0].row_count, 29)
        self.assertEqual(layout.tables[0].column_count, 4)
        self.assertEqual(layout.tables[0].page_number, 1)
        self.assertEqual(layout.tables[1].row_count, 6)
        self.assertEqual(layout.tables[1].column_count, 5)
        self.assertEqual(layout.tables[1].page_number, 1)
        layout = result[1]
        self.assertEqual(len(layout.tables), 1)
        self.assertEqual(layout.page_number, 2)
        self.assertEqual(layout.tables[0].row_count, 23)
        self.assertEqual(layout.tables[0].column_count, 5)
        self.assertEqual(layout.tables[0].page_number, 2)
        self.assertFormPagesHasValues(result)

    @FormRecognizerPreparer()
    @FormRecognizerClientPreparer()
    def test_content_selection_marks(self, client):
        poller = client.begin_recognize_content_from_url(form_url=self.selection_mark_url_pdf)
        result = poller.result()
        self.assertEqual(len(result), 1)
        layout = result[0]
        self.assertEqual(layout.page_number, 1)
        self.assertFormPagesHasValues(result)

    @FormRecognizerPreparer()
    @FormRecognizerClientPreparer(client_kwargs={"api_version": FormRecognizerApiVersion.V2_0})
    def test_content_selection_marks_v2(self, client):
        poller = client.begin_recognize_content_from_url(form_url=self.selection_mark_url_pdf)
        result = poller.result()
        self.assertEqual(len(result), 1)
        layout = result[0]
        self.assertEqual(layout.page_number, 1)
        self.assertFormPagesHasValues(result)

    @FormRecognizerPreparer()
    @FormRecognizerClientPreparer()
    def test_content_specify_pages(self, client):
        poller = client.begin_recognize_content_from_url(self.multipage_url_pdf, pages=["1"])
        result = poller.result()
        assert len(result) == 1

        poller = client.begin_recognize_content_from_url(self.multipage_url_pdf, pages=["1", "3"])
        result = poller.result()
        assert len(result) == 2

        poller = client.begin_recognize_content_from_url(self.multipage_url_pdf, pages=["1-2"])
        result = poller.result()
        assert len(result) == 2

        poller = client.begin_recognize_content_from_url(self.multipage_url_pdf, pages=["1-2", "3"])
        result = poller.result()
        assert len(result) == 3

    @FormRecognizerPreparer()
    @FormRecognizerClientPreparer()
    def test_content_reading_order(self, client):
        poller = client.begin_recognize_content_from_url(self.form_url_jpg, reading_order="natural")

        assert 'natural' == poller._polling_method._initial_response.http_response.request.query['readingOrder']
        result = poller.result()
        assert result

    @FormRecognizerPreparer()
    @FormRecognizerClientPreparer()
    def test_content_language_specified(self, client):
        poller = client.begin_recognize_content_from_url(self.form_url_jpg, language="de")
        assert 'de' == poller._polling_method._initial_response.http_response.request.query['language']
        result = poller.result()
        assert result

    @FormRecognizerPreparer()
    @FormRecognizerClientPreparer()
    def test_content_language_error(self, client):
        with pytest.raises(HttpResponseError) as e:
            client.begin_recognize_content_from_url(self.form_url_jpg, language="not a language")
        assert "NotSupportedLanguage" == e.value.error.code

    @FormRecognizerPreparer()
    @FormRecognizerClientPreparer(client_kwargs={"api_version": FormRecognizerApiVersion.V2_0})
    def test_content_language_v2(self, client):
        with pytest.raises(ValueError) as e:
            client.begin_recognize_content_from_url(self.form_url_jpg, language="en")
        assert "'language' is only available for API version V2_1 and up" in str(e.value)
