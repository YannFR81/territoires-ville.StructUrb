import os
d=os.path.dirname(os.path.abspath(__file__))
s=open(d+'/app.src.html').read()
for tag,f in [('ENGINE','engine.js'),('METHODE','methode.js'),('CATALOGUE','catalogue_data.js'),('APP','app.js')]:
    s=s.replace(f'/*{tag}*/',open(d+'/'+f).read().replace('</script>','<\\/script>'))
open(d+'/dimensionnement_chaussees.html','w').write(s); print(len(s)//1024,'Ko')
