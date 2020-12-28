package it.univaq.disim.sealabaq;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.springframework.web.servlet.handler.HandlerInterceptorAdapter;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.io.InputStream;
import java.util.List;
import java.util.Map;
import java.util.Random;

public class NoiseInjectionInterceptor extends HandlerInterceptorAdapter {
    private static final Log logger = LogFactory.getLog(NoiseInjectionInterceptor.class);

    private static final Random random = new Random(33);

    private static List<Noise> config;

    public NoiseInjectionInterceptor(InputStream stream) {
        try {
            ObjectMapper mapper = new ObjectMapper();
            config = mapper.readValue(stream, new TypeReference<List<Noise>>(){});

        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private Noise getNoise(HttpServletRequest request) {
        String requestURL = request.getRequestURI();
        String requestMethod = request.getMethod();
        for ( Noise noise : config ){
            String uriRegexp = noise.getUri() + ".*";
            if (requestURL.matches(uriRegexp) && requestMethod.equals(noise.getMethod()) ){
                return noise;
            }
        }
        return null;
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

        Noise noise = getNoise(request);
        if ( noise != null && noise.getDelay() > 0) {
            logger.info("Adding delay: " + noise.getDelay() + " with probability " + noise.getProb());
            if (random.nextFloat() < noise.getProb()) {
                addDelay(noise.getDelay());
                logger.info("Added : " + noise.getDelay() + "ms delay ");
            }
        }
        return true;
    }

}