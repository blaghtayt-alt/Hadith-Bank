"""Offline transport safety regressions using synthetic TEST source objects."""
import sys,socket,unittest,tempfile,json,gzip,hashlib,urllib.error,time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import import_deenhindi as m
from test_import_deenhindi import object_page
RAW=object_page('hadith', {'id':'TEST','collectionSlug':'muslim','hadithNumber':'103','textArabic':'TEST Arabic','translationHindi':'TEST हिन्दी'})
class Response:
 def __init__(self,url,body,status=200,mime='text/html'):self.url=url;self.body=body;self.status=status;self.headers={'Content-Type':'text/plain' if url.endswith('/robots.txt') and not body.lstrip().startswith(b'<') else mime}
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def geturl(self):return self.url
 def read(self,n):return self.body[:n]
class SafetyBoundaries(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);(self.root/'AGENTS.md').write_text('OFFLINE TEST FIXTURE ONLY')
  self.ws=self.root/m.IMPORT;self.ws.mkdir(parents=True)
  self.args=SimpleNamespace(root=self.root,max_records=1,delay_seconds=1.25,timeout_seconds=20,max_seconds=60,retry_errors=False)
  about=b'offline synthetic attribution fixture';ap=self.ws/'about.txt';ap.write_bytes(about)
  self.state={'schema':'deenhindi-import-state-v1','imported':{},'errors':{},'site_evidence':{'about':{'path':str(ap.relative_to(self.root)),'sha256':m.digest(about)}}}
  self.inventory={k:{'slug':k,'identifiers':['103'] if k=='muslim' else []} for k in m.BOOKS}
  self.calls=[];self.delays=[]
  self.write_state();m.write_json(self.ws/'inventory.json',self.inventory)
  self.net=patch.object(socket.socket,'connect',side_effect=AssertionError('NETWORK FORBIDDEN'));self.net.start()
 def tearDown(self):self.net.stop();self.tmp.cleanup()
 def write_state(self):m.write_json(self.ws/'state.json',self.state)
 def simulate(self,robots=b'User-agent: *\nAllow: /',page=RAW,error=None):
  def opener(req,timeout):
   self.calls.append(req.full_url)
   self.assertEqual(req.get_header('User-agent'),m.USER_AGENT)
   if error:raise error
   return Response(req.full_url,robots if req.full_url.endswith('/robots.txt') else page)
  with patch.object(m.urllib.request.OpenerDirector,'open',side_effect=opener),patch.object(m.time,'sleep',side_effect=self.delays.append):return m.run(self.args)
 def test_generic_challenge_robots_stops(self):
  r=self.simulate(robots=b'<title>Just a moment...</title><script src="/cdn-cgi/challenge-platform/x"></script>');self.assertTrue(r['blocked']);self.assertEqual(len(self.calls),1)
 def test_html_robots_stops(self):
  r=self.simulate(robots=b'<html>Unavailable</html>');self.assertTrue(r['blocked']);self.assertEqual(len(self.calls),1)
 def test_wildcard_disallow(self):
  r=self.simulate(robots=b'User-agent: *\nDisallow: /hadith/*');self.assertTrue(r['blocked']);self.assertEqual(len(self.calls),1)
 def test_specific_denial(self):
  r=self.simulate(robots=b'User-agent: *\nAllow: /\nUser-agent: HadithBankSourceImporter\nDisallow: /');self.assertTrue(r['blocked']);self.assertEqual(len(self.calls),1)
 def test_fractional_delay(self):
  r=self.simulate(robots=b'User-agent: *\nAllow: /\nCrawl-delay: 9.5');self.assertFalse(r['blocked']);self.assertGreater(self.delays[0],9.4)
 def test_request_rate_delay(self):
  r=self.simulate(robots=b'User-agent: *\nAllow: /\nRequest-rate: 2/19');self.assertFalse(r['blocked']);self.assertGreater(self.delays[0],9.4)
 def test_bad_rules_fail_closed(self):
  for rule in (b'User-agent: *\nRequest-rate: 1/0',b'User-agent: Hadith*\nAllow: /',b'User-agent: *\nCrawl-delay: nan',b'User-agent: *\nUnknown: yes',b'',b'User-agent: *\nDisallow: /h%61dith/'):
   with self.assertRaises(ValueError):m.ConservativeRobots(rule.decode())
 def test_generic_page_gate_stops(self):
  r=self.simulate(page=b'<title>Just a moment...</title><script src="/cdn-cgi/challenge-platform/x"></script>');self.assertTrue(r['blocked']);self.assertEqual(r['imported_count'],0)
 def test_encoded_split_markers_stop(self):
  for marker in (b'Veri<span>fy</span> you are human',b'/cdn-cgi/chal<!--x-->lenge-platform',b'&#47;cdn-cgi&#47;challenge-platform'):
   self.write_state();self.calls.clear()
   r=self.simulate(page=RAW+marker);self.assertEqual(len(self.calls),2);self.assertTrue(r['blocked']);self.assertEqual(r['imported_count'],0)
 def test_changed_final_destination_stops(self):
  for final in (m.BASE+'/api/hadith','https://other.invalid/','http://deenhindi.com/hadith/muslim/103'):
   with patch.object(m.urllib.request.OpenerDirector,'open',return_value=Response(final,RAW)):
    with self.assertRaises(m.Halt):m.Fetcher(self.root,1.25,20).get(m.BASE+'/hadith/muslim/103')
 def test_wrong_mime_stops(self):
  with patch.object(m.urllib.request.OpenerDirector,'open',return_value=Response(m.BASE+'/hadith/muslim/103',RAW,mime='application/json')):
   with self.assertRaises(m.Halt):m.Fetcher(self.root,1.25,20).get(m.BASE+'/hadith/muslim/103')
 def test_redirect_handler_never_returns_request(self):
  self.assertIsNone(m.NoSourceRedirect().redirect_request(None,None,302,'Found',{},m.BASE+'/api/hadith'))
 def test_http_redirect_persists_stop(self):
  r=self.simulate(error=urllib.error.HTTPError(m.BASE+'/robots.txt',302,'Found',{},None));self.assertTrue(r['blocked']);self.assertEqual(len(self.calls),1)
 def test_delay_over_deadline_never_requests(self):
  self.args.max_seconds=1;r=self.simulate(robots=b'User-agent: *\nCrawl-delay: 999999999');self.assertTrue(r['time_budget_exhausted']);self.assertEqual(len(self.calls),1)

 def test_noncanonical_routes_never_requested(self):
  routes=['/api','/_next','/%61pi','/hadith/../api','/hadith/muslim/..','/hadith/muslim/.','/hadith/muslim/103?x=1','/hadith/muslim/103?','/hadith/muslim/103#','/hadith/muslim/103#x','/hadith//muslim/103','/hadith/muslim/103/','/hadith/unknown/103','/profile','/page/other','/hadith/muslim/%31','/hadith/muslim/1;param','/hadith/muslim/1..2']
  urls=[m.BASE+r for r in routes]+[' '+m.BASE+'/robots.txt',m.BASE+'/robots.txt\n','https://deenhindi.com:443/robots.txt','https://user@deenhindi.com/robots.txt','https://DEENHINDI.com/robots.txt']
  with patch.object(m.urllib.request.OpenerDirector,'open',side_effect=AssertionError('must not request')) as request:
   for url in urls:
    with self.subTest(url=url):
     self.assertFalse(m.allowed_source_url(url))
     with self.assertRaises(ValueError):m.Fetcher(self.root,1.25,20).get(url)
     self.assertFalse(m.ConservativeRobots('User-agent: *\nAllow: /').can_fetch(m.USER_AGENT,url))
   request.assert_not_called()
 def test_exact_supported_routes(self):
  for route in ['/robots.txt','/page/about-us']+[f'/hadith/{slug}' for slug in m.BOOKS]+[f'/hadith/{slug}/{number}' for slug in m.BOOKS for number in ['103','1a','1.2','3-4','5_6']]:
   self.assertTrue(m.allowed_source_url(m.BASE+route),route)
 def test_query_denial_cannot_be_bypassed(self):
  rules='User-agent: *\nDisallow: /hadith/muslim/103?blocked=1'
  robot=m.ConservativeRobots(rules);url=m.BASE+'/hadith/muslim/103?blocked=1'
  self.assertFalse(robot.can_fetch(m.USER_AGENT,url))
  with self.assertRaises(ValueError):m.robots_policy(rules,url)
