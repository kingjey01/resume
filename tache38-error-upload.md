 curl.exe --limit-rate 800k -X POST -H "Authorization: Bearer x" -F "course_id=1" -F "summary_title=test" -F "audio_file=@test.aac;type=audio/aac" -w "\n---\nHTTP: %{http_code} | Time: %{time_total}s | Size envoyé: %{size_upload}\n" https://resumecours.gestionhospitaliare.site/api/courses/sessions/upload-audio/ -v
Note: Unnecessary use of -X or --request, POST is already inferred.
* Host resumecours.gestionhospitaliare.site:443 was resolved.
* IPv6: (none)
* IPv4: 180.149.197.29
*   Trying 180.149.197.29:443...
* schannel: disabled automatic use of client certificate
* ALPN: curl offers http/1.1
* ALPN: server accepted http/1.1
*    Subject: CN=resumecours.gestionhospitaliare.site
*    Issuer: C=US, O=Let's Encrypt, CN=YR2
*    Version: 2
*    Serial Number: 06:03:a0:5e:d3:3e:44:62:8c:86:c1:d6:70:d0:6c:e2:59:15:
*    Signature Algorithm: sha256WithRSAEncryption
*    Start Date: 2026-10-11 12:05:05 GMT
*    Expire Date: 2027-01-09 12:05:04 GMT
*    Public Key Algorithm: rsaEncryption
*    RSA Public Key (2048 bits)
*    rsa(n): bb:1e:a7:34:bf:b9:aa:d9:97:a8:51:e4:ac:e3:b2:74:51:2c:97:a5:89:9a:5c:d6:5e:0a:d2:1a:6a:54:64:a3:c7:97:b1:43:ec:01:87:bb:18:e3:46:a6:6e:ea:2f:f2:39:08:79:5f:e9:a5:ed:61:d2:0f:3d:3a:9e:9c:d1:6b:18:04:bb:2b:9b:77:dd:14:fd:7c:18:c4:3b:73:ce:10:7e:d4:0e:b6:25:77:27:6b:06:42:86:cf:1b:b1:56:08:84:ee:5d:e6:b5:8d:7a:ff:1e:04:88:91:d8:d4:ae:34:94:b1:8c:4c:a3:90:47:9e:6d:ae:06:9a:4a:f6:9c:95:be:42:95:fd:48:a2:8c:d8:bb:ba:e5:5a:17:f4:b4:5f:13:19:ba:9c:91:88:14:81:96:c9:f0:f0:a9:97:e7:8a:a7:c3:1e:0f:a0:ed:ae:63:44:ee:ee:18:f6:ae:c5:02:ae:88:de:a0:f3:8d:b4:e4:94:0b:5e:0d:e3:d1:cc:78:86:23:10:be:cc:6b:ee:b5:82:83:65:01:ba:bc:50:7f:40:d2:cf:1c:a6:14:9f:0e:09:9a:57:eb:02:aa:a1:ce:26:54:6d:3c:b3:07:b2:5a:9c:d8:15:41:f2:37:fb:3e:be:49:9c:ce:c9:c4:e1:58:e6:1e:2c:92:9c:d8:8a:07:
*    rsa(e): 0x10001
a
//e1UsgCeDGYu52ZyCIPNuFZI99nMsx9QNYZqk959De9TFJVVn1l++k0PDLYwhPg
3BVE8v2O9uzc9BbqDoJMWXsMBJF+xQ==
-----END CERTIFICATE-----

* Established connection to resumecours.gestionhospitaliare.site (180.149.197.29 port 443) from 192.168.1.69 port 60450
* using HTTP/1.x
> POST /api/courses/sessions/upload-audio/ HTTP/1.1
> Host: resumecours.gestionhospitaliare.site
> User-Agent: curl/8.21.0
> Accept: */*
> Authorization: Bearer x
> Content-Length: 65043516
> Content-Type: multipart/form-data; boundary=------------------------W9QZtqlh4zSyXP6FFm8Jt0
> Expect: 100-continue
>
* schannel: remote party requests renegotiation
* schannel: renegotiating SSL/TLS connection
*    Subject: CN=resumecours.gestionhospitaliare.site
*    Issuer: C=US, O=Let's Encrypt, CN=YR2
*    Version: 2
*    Serial Number: 06:03:a0:5e:d3:3e:44:62:8c:86:c1:d6:70:d0:6c:e2:59:15:
*    Signature Algorithm: sha256WithRSAEncryption
*    Start Date: 2026-10-11 12:05:05 GMT
*    Expire Date: 2027-01-09 12:05:04 GMT
*    Public Key Algorithm: rsaEncryption
*    RSA Public Key (2048 bits)
*    rsa(n): 
-----END CERTIFICATE-----

* schannel: SSL/TLS connection renegotiated
* schannel: remote party requests renegotiation
* schannel: renegotiating SSL/TLS connection
*    Subject: CN=resumecours.gestionhospitaliare.site
*    Issuer: C=US, O=Let's Encrypt, CN=YR2
*    Version: 2
*    Serial Number: 06:03:a0:5e:d3:3e:44:62:8c:86:c1:d6:70:d0:6c:e2:59:15:
*    Signature Algorithm: sha256WithRSAEncryption
*    Start Date: 2026-10-11 12:05:05 GMT
*    Expire Date: 2027-01-09 12:05:04 GMT
*    Public Key Algorithm: rsaEncryption
*    RSA Public Key (2048 bits)
*    rsa(n): 
//e1UsgCeDGYu52ZyCIPNuFZI99nMsx9QNYZqk959De9TFJVVn1l++k0PDLYwhPg
3BVE8v2O9uzc9BbqDoJMWXsMBJF+xQ==
-----END CERTIFICATE-----

* schannel: SSL/TLS connection renegotiated
< HTTP/1.1 100 Continue
<
PS C:\Users\USER> curl.exe -o test.aac https://resumecours.gestionhospitaliare.site/media/audio_sessions/gestion_des_risques_EutTpTu.aac
  % Total    % Received % Xferd  Average Speed  Time    Time    Time   Current
                                 Dload  Upload  Total   Spent   Left   Speed
100 62.02M 100 62.02M   0      0 253.7k      0   04:10   04:10         267.6k
PS C:\Users\USER>