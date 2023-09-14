SEARCH_QUERY_1 = ('search index=* src_ip="192.168.131.176" '
                  'earliest=-1d latest=now '
                  'Account_Name!="" '
                  '| dedup Account_Name | table Account_Name'
                  )

EVENT_CODE = 4662
SEARCH_QUERY_2 = (f'search index=* EventCode={EVENT_CODE} Account_Name!="" '
                  '| stats count by Account_Name, Logon_ID '
                  '| sort -count | head 15'
                  )

MAX_EVENT_COUNT = 500_000
