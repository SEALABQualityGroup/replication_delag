package it.univaq.disim.sealabaq;


import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.opentracing.Span;
import io.opentracing.Tracer;
import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.springframework.util.concurrent.ListenableFuture;
import org.springframework.web.servlet.handler.HandlerInterceptorAdapter;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.io.InputStream;
import java.util.List;
import java.util.Map;
import java.util.Random;

public class LatencyInjectionInterceptor extends HandlerInterceptorAdapter {

    private static final Log logger = LogFactory.getLog(LatencyInjectionInterceptor.class);

    private static final String tagKey = "experiment";

    private static final Random random = new Random(33);

    private static final int randomBound = 10;

    private static List<List<Latency>> config;


    private Tracer tracer;

    public LatencyInjectionInterceptor(Tracer tracer, InputStream stream) {
        this.tracer = tracer;
        try {
            ObjectMapper mapper = new ObjectMapper();
            config = mapper.readValue(stream, new TypeReference<List<List<Latency>>>(){});

        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private String randomNumber() {
        return Integer.toString(random.nextInt(randomBound));
    }

    private void createBaggageItemIfNotExists(Span span) {
        if (span.getBaggageItem(tagKey) == null) {
            span.setBaggageItem(tagKey, randomNumber());
        }
    }

    private int getDelay(HttpServletRequest request, int experimentNumber) {
        String requestURL = request.getRequestURI();
        String requestMethod = request.getMethod();
        if( experimentNumber < config.size()) {
            List<Latency> pattern = config.get(experimentNumber);
            for (Latency latency : pattern){
                String uriRegexp = latency.getUri() + ".*";
                if (requestURL.matches(uriRegexp) && requestMethod.equals(latency.getMethod()) ){
                    return latency.getDelay();
                }

            }

        }
        return 0;
    }


    private void addDelay(int delay) {
        try {
            Thread.sleep(delay);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        logger.info("Request URI: " + request.getRequestURI());

        Span span = tracer.activeSpan();
        if (span != null) {
            createBaggageItemIfNotExists(span);
            int experimentNumber = Integer.parseInt(span.getBaggageItem(tagKey));
            span.setTag(tagKey, experimentNumber);
            logger.info("Experiment tag: " + experimentNumber);
            int delay = getDelay(request, experimentNumber);
            if (delay > 0) {
                logger.info("Adding delay: " + delay);
                addDelay(delay);
            }
        }
        return true;
    }

}
