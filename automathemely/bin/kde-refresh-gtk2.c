#include <gtk/gtk.h>
//#include <gdk/gdkx.h>

// This has to be compiled with `pkg-config --cflags --libs gtk+-2.0`

GdkEventClient createEvent()
{
    GdkEventClient event;
    event.type = GDK_CLIENT_EVENT;
    event.send_event = TRUE;
    event.window = NULL;
    event.message_type = gdk_atom_intern("_GTK_READ_RCFILES", FALSE);
    event.data_format = 8;
    
    return event;
}

int main(int argc, char** argv)
{
    gtk_init(&argc, &argv);
    
    GdkEventClient event = createEvent();
	// This function isn't available in PyGObject so that's why we need this additional c program
    gdk_event_send_clientmessage_toall((GdkEvent *)&event);
    return 0;
}