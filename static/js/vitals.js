(function(){
  function sendToAnalytics(metric){
    try{
      const body = JSON.stringify({[metric.name]: metric.value});
      navigator.sendBeacon('/analytics/vitals', body);
    }catch(e){/* no-op */}
  }
  webVitals.onCLS(sendToAnalytics);
  webVitals.onFID(sendToAnalytics);
  webVitals.onLCP(sendToAnalytics);
  webVitals.onINP(sendToAnalytics);
  webVitals.onTTFB(sendToAnalytics);
})();
