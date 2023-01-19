package orca.stordis.backend.orca_backend;

import java.net.http.HttpHeaders;
import java.security.cert.X509Certificate;
import java.util.Base64;
import java.util.logging.Logger;

import javax.net.ssl.SSLContext;
import javax.net.ssl.TrustManager;
import javax.net.ssl.X509TrustManager;

import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.http.client.HttpComponentsClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

import org.apache.http.conn.ssl.NoopHostnameVerifier;
// import org.apache.http.impl.client.CloseableHttpClient;
// import org.apache.http.impl.client.HttpClients;

@SpringBootApplication
public class OrcaBackendApplication {
	private static final Logger logger = Logger.getLogger(GrpcClient.class.getName());

	public static void main(String[] args) {
		SpringApplication.run(OrcaBackendApplication.class, args);
		for (int i = 0; i < 10; i++) {
			GrpcClient.gnmi_example_call();
			try {
				Thread.sleep(5*1000);
			} catch (InterruptedException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
		}
	}
}
