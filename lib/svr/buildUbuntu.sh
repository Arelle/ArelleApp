python3.4 setup.py build_exe
rm -fR /usr/lib/cgi-bin/arelleApp/*
rm -fR /var/www/html/arelleApp/*
cp -R build/exe.linux-x86_64-3.4/* /usr/lib/cgi-bin/arelleApp
cp ../../lib/index.html /var/www/html/arelleApp
cp -R ../../lib/cli /var/www/html/arelleApp
cp -R ../../lib/UI /var/www/html/arelleApp
