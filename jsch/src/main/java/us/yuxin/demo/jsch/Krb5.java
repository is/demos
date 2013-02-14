package us.yuxin.demo.jsch;

import com.jcraft.jsch.Channel;
import com.jcraft.jsch.JSch;
import com.jcraft.jsch.JSchException;
import com.jcraft.jsch.Session;
import com.jcraft.jsch.UserInfo;

public class Krb5 {
  public static void main(String argv[]) throws JSchException {

    String host = argv[0];
    int port = Integer.parseInt(argv[1]);

    JSch jsch = new JSch();
    Session session = jsch.getSession("root", host, port);
    session.setUserInfo(new NonInteractiveUserInfo());
    session.connect(30000);
    Channel channel = session.openChannel("shell");
    channel.setInputStream(System.in);
    channel.setOutputStream(System.out);
    channel.connect(3 * 1000);
  }

  public static class NonInteractiveUserInfo implements UserInfo {

    @Override
    public String getPassphrase() {
      return null;
    }

    @Override
    public String getPassword() {
      return null;
    }

    @Override
    public boolean promptPassword(String message) {
      return false;
    }

    @Override
    public boolean promptPassphrase(String message) {
      return false;
    }

    @Override
    public boolean promptYesNo(String message) {
      return false;
    }

    @Override
    public void showMessage(String message) {
    }
  }
}
