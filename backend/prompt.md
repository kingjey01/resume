
[root@vps114384 backend]# /home/jey/resumecours.gestionhospitaliare.site/env39/bin/python -c "import   os,django;os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.settings');django.setup();from django.conf import
>   settings;print('SETTINGS:',settings.SETTINGS_MODULE,'| analytics dans apps:', 'analytics' in settings.INSTALLED_APPS);from datetime import   datetime;from analytics.periods import day_key;print('day_key(naive):',day_key(datetime(2026,7,15,10,0)))"
  File "<string>", line 1
    import   os,django;os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.settings');django.setup();from django.conf import
                                                                                                                                 ^
SyntaxError: invalid syntax
[root@vps114384 backend]#






