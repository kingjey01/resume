WSGISocketPrefix /var/run/wsgi 
WSGIPythonHome "/home/jey/resumecours.gestionhospitaliare.site/env"
WSGIPythonPath "/home/jey/resumecours.gestionhospitaliare.site/backend"


<VirtualHost 180.149.197.29:443>
	ServerName resumecours.gestionhospitaliare.site
	ServerAlias www.resumecours.gestionhospitaliare.site
	ServerAdmin webmaster@resumecours.gestionhospitaliare.site
	DocumentRoot /home/jey/resumecours.gestionhospitaliare.site
	UseCanonicalName Off
	ScriptAlias /cgi-bin/ /home/jey/resumecours.gestionhospitaliare.site/cgi-bin/

	#CustomLog /usr/local/apache/domlogs/resumecours.gestionhospitaliare.site.bytes bytes
	#CustomLog /usr/local/apache/domlogs/resumecours.gestionhospitaliare.site.log combined
	#ErrorLog /usr/local/apache/domlogs/resumecours.gestionhospitaliare.site.error.log

	# Custom settings are loaded below this line (if any exist)
	# IncludeOptional "/usr/local/apache/conf/userdata/jey/resumecours.gestionhospitaliare.site/*.conf"

	SSLEngine on
	SSLCertificateFile /etc/pki/tls/certs/resumecours.gestionhospitaliare.site.cert
	SSLCertificateKeyFile /etc/pki/tls/private/resumecours.gestionhospitaliare.site.key
	SSLCertificateChainFile /etc/pki/tls/certs/resumecours.gestionhospitaliare.site.bundle
	SetEnvIf User-Agent ".*MSIE.*" nokeepalive ssl-unclean-shutdown

    Alias /static /home/jey/resumecours.gestionhospitaliare.site/backend/staticfiles
	<Directory "/home/jey/resumecours.gestionhospitaliare.site/backend/staticfiles">
	Options FollowSymLinks
		Order allow,deny
		Allow from all
		Require all granted
	</Directory>

	Alias /media /home/jey/resumecours.gestionhospitaliare.site/backend/media
	<Directory "/home/jey/resumecours.gestionhospitaliare.site/backend/media">
		Options FollowSymLinks
		Order allow,deny
		Allow from all
		Require all granted
	</Directory>

	ErrorLog /home/jey/resumecours.gestionhospitaliare.site/backend/log/apis_error.log
	CustomLog /home/jey/resumecours.gestionhospitaliare.site/backend/log/apis_access.log combined

#WSGIDaemonProcess resume python-#path=/home/jey/resumecours.gestionhospitaliare.site/backend/:/home/jey/resumecours.gestionhospitaliare.#site/env/lib/python3.7/site-packages
#	WSGIProcessGroup resume
	
WSGIDaemonProcess monsite python-home=/root/.pyenv/versions/3.10.14 \
                      python-path=/home/jey/resumecours.gestionhospitaliare.site/backend \
                      processes=2 threads=5
    WSGIProcessGroup resume
WSGIApplicationGroup %{GLOBAL}

WSGIPassAuthorization On

WSGIScriptAlias / /home/jey/resumecours.gestionhospitaliare.site/backend/backend/wsgi.py
<Directory "/home/jey/resumecours.gestionhospitaliare.site/backend/backend">
		<Files wsgi.py>
			Require all granted
		</Files>
</Directory>

	<IfModule mod_userdir.c>
		UserDir disabled
		UserDir enabled jey
	</IfModule>

	<IfModule mod_suexec.c>
		SuexecUserGroup jey jey
	</IfModule>

	<IfModule mod_suphp.c>
		suPHP_UserGroup jey jey
		suPHP_ConfigPath /home/jey
	</IfModule>

	<IfModule mod_ruid2.c>
		RMode config
		RUidGid jey jey
	</IfModule>

	<IfModule itk.c>
		AssignUserID jey jey
	</IfModule>

	<Directory "/home/jey/resumecours.gestionhospitaliare.site">
		Options -Indexes -FollowSymLinks +SymLinksIfOwnerMatch
		AllowOverride All Options=ExecCGI,Includes,IncludesNOEXEC,Indexes,MultiViews,SymLinksIfOwnerMatch
		SSLRequireSSL
	</Directory>

</VirtualHost>

<VirtualHost 180.149.197.29:443>
	ServerName webmail.resumecours.gestionhospitaliare.site

	SSLEngine on
	SSLCertificateFile /etc/pki/tls/certs/resumecours.gestionhospitaliare.site.cert
	SSLCertificateKeyFile /etc/pki/tls/private/resumecours.gestionhospitaliare.site.key
	SSLCertificateChainFile /etc/pki/tls/certs/resumecours.gestionhospitaliare.site.bundle
	SetEnvIf User-Agent ".*MSIE.*" nokeepalive ssl-unclean-shutdown

	<IfModule mod_proxy.c>
		ProxyRequests Off
		ProxyPreserveHost On
		ProxyVia Full
		ProxyPass / http://127.0.0.1:2095/
		ProxyPassReverse / http://127.0.0.1:2095/

		<Proxy *>
			AllowOverride All
		</Proxy>
	</IfModule>

	<IfModule mod_security2.c>
		SecRuleEngine Off
	</IfModule>

</VirtualHost>

<VirtualHost 180.149.197.29:443>
	ServerName mail.resumecours.gestionhospitaliare.site

	SSLEngine on
	SSLCertificateFile /etc/pki/tls/certs/resumecours.gestionhospitaliare.site.cert
	SSLCertificateKeyFile /etc/pki/tls/private/resumecours.gestionhospitaliare.site.key
	SSLCertificateChainFile /etc/pki/tls/certs/resumecours.gestionhospitaliare.site.bundle
	SetEnvIf User-Agent ".*MSIE.*" nokeepalive ssl-unclean-shutdown

	<IfModule mod_proxy.c>
		ProxyRequests Off
		ProxyPreserveHost On
		ProxyVia Full
		ProxyPass / http://127.0.0.1:2095/
		ProxyPassReverse / http://127.0.0.1:2095/

		<Proxy *>
			AllowOverride All
		</Proxy>
	</IfModule>

	<IfModule mod_security2.c>
		SecRuleEngine Off
	</IfModule>

</VirtualHost>

<VirtualHost 180.149.197.29:443>
	ServerName cpanel.resumecours.gestionhospitaliare.site

	SSLEngine on
	SSLCertificateFile /etc/pki/tls/certs/resumecours.gestionhospitaliare.site.cert
	SSLCertificateKeyFile /etc/pki/tls/private/resumecours.gestionhospitaliare.site.key
	SSLCertificateChainFile /etc/pki/tls/certs/resumecours.gestionhospitaliare.site.bundle
	SetEnvIf User-Agent ".*MSIE.*" nokeepalive ssl-unclean-shutdown

	<IfModule mod_proxy.c>
		SSLProxyEngine on
		SSLProxyVerify none
		SSLProxyCheckPeerCN off
		SSLProxyCheckPeerName off
		SSLProxyCheckPeerExpire off
		ProxyRequests Off
		ProxyPreserveHost On
		ProxyVia Full

		RewriteEngine on

		RewriteRule ^/roundcube$ /roundcube/ [R]
		ProxyPass /roundcube/ https://127.0.0.1:2031/roundcube/
		ProxyPassReverse /roundcube https://127.0.0.1:2031/roundcube/

		RewriteRule ^/pma$ /pma/ [R]
		ProxyPass /pma/ https://127.0.0.1:2031/pma/
		ProxyPassReverse /pma https://127.0.0.1:2031/pma/

		ProxyPass / https://127.0.0.1:2083/
		ProxyPassReverse / https://127.0.0.1:2083/

		<Proxy *>
			AllowOverride All
		</Proxy>
	</IfModule>

	<IfModule mod_security2.c>
		SecRuleEngine Off
	</IfModule>
	
</VirtualHost>