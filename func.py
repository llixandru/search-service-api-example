# coding: utf-8
# Copyright (c) 2016, 2020, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl
# or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

import io
import json
import oci
import requests
from fdk import response
import os
import base64


def handler(ctx, data: io.BytesIO = None):
    try:
        body = json.loads(data.getvalue())
    except Exception:
        raise Exception()
    resp = search(body)
    return response.Response(
        ctx,
        response_data=json.dumps(resp),
        headers={"Content-Type": "application/json"}
    )


def search(body):
    signer = oci.auth.signers.get_resource_principals_signer()
    try:

        # Read resource principal data and get tenancy OCID
        rpst = open(os.environ.get('OCI_RESOURCE_PRINCIPAL_RPST'), "r")
        env = rpst.read()
        payload = env.split('.')[1]
        base64_bytes = payload.encode('ascii')
        message_bytes = base64.b64decode(base64_bytes)
        payloadDecoded = message_bytes.decode('ascii')

        tenancy = json.loads(payloadDecoded)['res_tenant']

        # Construct the region subscription URL
        endpoint_regionSub = 'https://identity.eu-frankfurt-1.oraclecloud.com/20160918/tenancies/' + \
            tenancy + '/regionSubscriptions'

        # Get subscribed regions for the tenancy
        regionSub = requests.get(endpoint_regionSub, auth=signer)
        regionSub = json.loads(json.dumps(regionSub.json()))

        # Call the Search Service API and get the query data
        result = []
        for region in regionSub:
            if region['status'] == 'READY':
                endpoint = 'https://query.' + \
                    region['regionName'] + \
                    '.oci.oraclecloud.com/20180409/resources'
                output = requests.post(endpoint, json=body, auth=signer)
                if output:
                    output = json.loads(json.dumps(output.json()))
                    result = result + output['items']
    except Exception as e:
        result = "Failed: " + str(e)
    return result
