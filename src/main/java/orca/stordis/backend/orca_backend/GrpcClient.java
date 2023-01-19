/*
 * Copyright 2015 The gRPC Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package orca.stordis.backend.orca_backend;

import io.grpc.Grpc;
import io.grpc.InsecureChannelCredentials;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import io.grpc.Metadata;
import io.grpc.stub.MetadataUtils;
import io.grpc.stub.StreamObserver;

import java.util.logging.Logger;

import com.github.gnmi.proto.GetRequest;
import com.github.gnmi.proto.GetResponse;
import com.github.gnmi.proto.Path;
import com.github.gnmi.proto.PathElem;
import com.github.gnmi.proto.gNMIGrpc;
import com.github.gnmi.proto.gNMIGrpc.gNMIStub;

public class GrpcClient {
  private static final Logger logger = Logger.getLogger(GrpcClient.class.getName());

  public static void gnmi_example_call() {
    Metadata headers = new Metadata();
    headers.put(Metadata.Key.of("username", Metadata.ASCII_STRING_MARSHALLER), "admin");
    headers.put(Metadata.Key.of("password", Metadata.ASCII_STRING_MARSHALLER), "YourPaSsWoRd");
    ManagedChannelBuilder<?> channelBuilder
        = Grpc.newChannelBuilderForAddress("10.10.130.15", 8080, InsecureChannelCredentials.create());
        //.enableRetry().keepAliveTime(5, TimeUnit.MINUTES).idleTimeout(5, TimeUnit.MINUTES);

    ManagedChannel channel = channelBuilder.build();
    gNMIStub gnmiStub = gNMIGrpc.newStub(channel);
    gnmiStub=gnmiStub.withInterceptors(MetadataUtils.newAttachHeadersInterceptor(headers));
    
    PathElem pathElem=PathElem.newBuilder().setName("/openconfig-interfaces:interfaces/interface[name=Ethernet0]/config").build();
    Path path=Path.newBuilder().addElem(pathElem).build();
    GetRequest getRequest = GetRequest.newBuilder().addPath(path).build();

    System.out.println(getRequest.toString());
    gnmiStub.get(getRequest, responseObserver);
  }

  static io.grpc.stub.StreamObserver<GetResponse> responseObserver = new StreamObserver<GetResponse>() {
    @Override
    public void onNext(GetResponse value) {
      System.out.println(value.toString());
    }

    @Override
    public void onError(Throwable t) {
      t.printStackTrace();
    }

    @Override
    public void onCompleted() {
      System.out.println("completed");
    }
  };

}
