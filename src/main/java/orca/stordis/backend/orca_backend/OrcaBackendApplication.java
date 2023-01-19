package orca.stordis.backend.orca_backend;

import java.util.logging.Logger;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;


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
